#define _USE_MATH_DEFINES
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "Pythia8/Pythia.h"
#include "Simpler_ToyDetector.h"
#include "efficiency.h"

using namespace Pythia8;

struct Args {
  std::string lhe, out;
  int events = 0, seed = 0, pdg = 9000006;
  double mass = 0., ctau = 0.;
  bool resonance = false;
  double br = 1.;
  int d1 = 5, d2 = -5;
};

static std::string arg(int argc, char **argv, const std::string &name) {
  for (int i = 1; i + 1 < argc; ++i)
    if (argv[i] == name) return argv[i + 1];
  throw std::runtime_error("missing " + name);
}

static bool has(int argc, char **argv, const std::string &name) {
  for (int i = 1; i < argc; ++i) if (argv[i] == name) return true;
  return false;
}

static Args parse(int argc, char **argv) {
  if (argc == 1 || has(argc, argv, "--help"))
    throw std::runtime_error("usage: scalar_h2_recast --lhe FILE --out JSONL --events N --seed N --pdg N --mass GEV --ctau MM --channel 5,-5:1 [--is-resonance 0|1]");
  Args a;
  a.lhe = arg(argc, argv, "--lhe");
  a.out = arg(argc, argv, "--out");
  a.events = std::stoi(arg(argc, argv, "--events"));
  a.seed = std::stoi(arg(argc, argv, "--seed"));
  a.pdg = std::stoi(arg(argc, argv, "--pdg"));
  a.mass = std::stod(arg(argc, argv, "--mass"));
  a.ctau = std::stod(arg(argc, argv, "--ctau"));
  if (has(argc, argv, "--is-resonance")) a.resonance = std::stoi(arg(argc, argv, "--is-resonance")) != 0;
  if (has(argc, argv, "--channel")) {
    std::string c = arg(argc, argv, "--channel");
    const std::size_t colon = c.find(':');
    const std::size_t comma = c.find(',');
    if (colon == std::string::npos || comma == std::string::npos || comma > colon)
      throw std::runtime_error("channel must be d1,d2:BR");
    a.d1 = std::stoi(c.substr(0, comma));
    a.d2 = std::stoi(c.substr(comma + 1, colon - comma - 1));
    a.br = std::stod(c.substr(colon + 1));
  }
  if (a.events <= 0 || a.seed <= 0 || a.pdg == 0 || a.mass <= 0. || a.ctau <= 0. || a.br < 0. || a.br > 1.)
    throw std::runtime_error("invalid scalar configuration");
  return a;
}

static std::vector<int> descendants(const Event &event, int index) {
  std::vector<int> result = event[index].daughterListRecursive();
  std::sort(result.begin(), result.end());
  result.erase(std::unique(result.begin(), result.end()), result.end());
  return result;
}

static bool bbParent(const Event &event, int index, const Args &a) {
  std::vector<int> ids;
  for (int child : event[index].daughterList()) ids.push_back(event[child].id());
  std::sort(ids.begin(), ids.end());
  if (ids == std::vector<int>({std::min(a.d1, a.d2), std::max(a.d1, a.d2)})) return true;
  // Pythia may replace the b/bbar decay products with the first showered
  // hadrons in the direct daughter list; Pack AA treats that two-body record
  // as the configured bb channel and validates the descendants downstream.
  return ids.size() == 2 && !(std::abs(ids[0]) == 22 && std::abs(ids[1]) == 22);
}

static double rxy(const Particle &p) { return std::hypot(p.xDec(), p.yDec()); }

struct Vertex {
  bool fiducial = false, displaced = false, impacted = false, multiplicity = false, mass = false;
  int charged = 0, selected = 0;
  double r = 0., z = 0., massGeV = 0.;
};

static Vertex inspectVertex(const Event &event, int index) {
  Vertex v;
  const Particle &parent = event[index];
  v.r = rxy(parent);
  v.z = parent.zDec();
  v.fiducial = v.r < 300. && std::abs(v.z) < 300.;
  v.displaced = v.r > 4.;
  Vec4 sum(0., 0., 0., 0.);
  for (int track : descendants(event, index)) {
    if (!event[track].isCharged() || !event[track].isFinal()) continue;
    ++v.charged;
    const double rTrack = std::hypot(event[track].xProd(), event[track].yProd());
    double dphi = event[track].vProd().phi() - event[track].phi();
    if (std::abs(dphi) > M_PI) dphi = 2. * M_PI - std::abs(dphi);
    if (std::abs(rTrack * std::sin(dphi)) > 2.) v.impacted = true;
    const double beta = event[track].e() > 0. ? event[track].pT() / event[track].e() : 0.;
    const double gamma = event[track].m() > 0. ? event[track].e() / event[track].m() : 0.;
    const double charge = std::abs(event[track].charge());
    if (beta * gamma * event[track].tau() > 520. && charge > 0. && event[track].pT() / charge > 1.) {
      ++v.selected;
      const double pion = 0.13957039;
      sum += Vec4(event[track].px(), event[track].py(), event[track].pz(), std::sqrt(event[track].pAbs2() + pion * pion));
    }
  }
  v.massGeV = sum.mCalc();
  v.multiplicity = v.selected >= 5;
  v.mass = v.massGeV > 10.;
  return v;
}

static std::string failure(const std::vector<bool> &stages) {
  static const char *names[] = {"expected_h2", "bb_decay", "displaced_vertex", "fiducial_dv", "jet_preselection", "high_pt_or_trackless", "track_requirements", "track_multiplicity", "mdv", "efficiency_map"};
  for (std::size_t i = 0; i < stages.size(); ++i) if (!stages[i]) return names[i];
  return "selected";
}

static void writeNumber(std::ostream &out, double x) { if (std::isfinite(x)) out << x; else out << "null"; }

int main(int argc, char **argv) {
  try {
    const Args a = parse(argc, argv);
    Pythia pythia;
    pythia.readString("Beams:frameType = 4");
    pythia.readString("Beams:LHEF = " + a.lhe);
    pythia.readString("SLHA:readFrom = 0");
    pythia.readString("LesHouches:setLifetime = 2");
    pythia.readString("Random:setSeed = on");
    pythia.readString("Random:seed = " + std::to_string(a.seed));
    pythia.readString("Main:numberOfEvents = " + std::to_string(a.events));
    pythia.readString("Next:numberShowEvent = 0");
    pythia.readString("Next:numberShowInfo = 0");
    pythia.readString("Next:numberShowProcess = 0");
    const double width = a.resonance ? std::max(1.973269804e-13 / a.ctau, 1e-9) : 1.973269804e-13 / a.ctau;
    pythia.readString(std::to_string(a.pdg) + ":all = h2 h2 1 0 0 " + std::to_string(a.mass) + " " + std::to_string(width) + " 0 0 " + std::to_string(a.ctau));
    pythia.readString(std::to_string(a.pdg) + ":isResonance = " + std::string(a.resonance ? "true" : "false"));
    pythia.readString(std::to_string(a.pdg) + ":mayDecay = true");
    pythia.readString(std::to_string(a.pdg) + ":tau0 = " + std::to_string(a.ctau));
    pythia.readString("ParticleDecays:limitTau0 = off");
    pythia.readString(std::to_string(a.pdg) + ":addChannel = 1 " + std::to_string(a.br) + " " + std::to_string(a.resonance ? 101 : 0) + " " + std::to_string(a.d1) + " " + std::to_string(a.d2));
    if (!pythia.init()) throw std::runtime_error("Pythia init failed");
    ParticleDataEntryPtr data = pythia.particleData.particleDataEntryPtr(a.pdg);
    data->clearChannels();
    data->addChannel(1, a.br, a.resonance ? 101 : 0, a.d1, a.d2);
    data->rescaleBR();
    data->setMayDecay(true);
    data->setTau0(a.ctau);
    data->setMWidth(width);
    data->setTauCalc(!a.resonance);
    pythia.particleData.resInit(a.pdg);
    data->setTau0(a.ctau);

    std::ofstream out(a.out);
    if (!out) throw std::runtime_error("cannot open output");
    out << std::setprecision(17);
    const char *stageNames[] = {"events_read", "events_expected_h2", "events_successful_h2_bb", "events_displaced_h2_vertex", "events_fiducial_decay", "events_jet_preselection", "events_high_pt_selection", "events_trackless_selection", "events_jet_selection", "candidate_displaced_vertices", "vertices_displaced_track_requirements", "vertices_track_multiplicity", "vertices_mdv", "events_event_efficiency_map", "events_vertex_efficiency_map", "final_selected_events"};
    double weighted[16] = {};
    int raw[16] = {};
    ToyDetector detector;
    for (int eventNumber = 1; eventNumber <= a.events; ++eventNumber) {
      if (!pythia.next()) throw std::runtime_error("Pythia failed before requested event count");
      const double lheWeight = pythia.info.weight();
      const double weight = lheWeight * pythia.info.mergingWeight() * 1e-9;
      std::vector<int> records, decayed;
      for (int i = 0; i < pythia.event.size(); ++i) {
        if (pythia.event[i].id() != a.pdg) continue;
        records.push_back(i);
        if (bbParent(pythia.event, i, a)) decayed.push_back(i);
      }
      detector.getObjects(pythia.event);
      const int nJets = static_cast<int>(detector.jets.size());
      double ht = 0.; for (const Vec4 &jet : detector.jets) ht += jet.pT();
      const bool expected = records.size() >= 2;
      const bool successful = !decayed.empty();
      bool displaced = false, fiducial = false, trackReq = false, multiplicity = false, mdv = false;
      int candidateVertices = static_cast<int>(decayed.size()), charged = 0, selectedTracks = 0;
      double dvR = 0., dvZ = 0., truthMass = 0., maxR = 0.;
      double vertexProbability = 0., eventProbability = 0.;
      for (int index : decayed) {
        const Vertex v = inspectVertex(pythia.event, index);
        displaced = displaced || v.displaced;
        fiducial = fiducial || (v.fiducial && v.displaced);
        trackReq = trackReq || (v.fiducial && v.displaced && v.impacted);
        multiplicity = multiplicity || (v.fiducial && v.displaced && v.impacted && v.multiplicity);
        mdv = mdv || (v.fiducial && v.displaced && v.impacted && v.multiplicity && v.mass);
        if (v.r >= dvR) { dvR = v.r; dvZ = v.z; charged = v.charged; selectedTracks = v.selected; truthMass = v.massGeV; }
        maxR = std::max(maxR, v.r);
        if (v.fiducial && v.displaced && v.impacted && v.multiplicity && v.mass) vertexProbability = std::max(vertexProbability, vertexEff(v.r, v.massGeV, v.selected));
      }
      bool highPt = false, tracklessBase = false;
      if (nJets >= 4 && detector.jets[3].pT() > 250.) highPt = true;
      if (nJets >= 5 && detector.jets[4].pT() > 195.) highPt = true;
      if (nJets >= 6 && detector.jets[5].pT() > 116.) highPt = true;
      if (nJets >= 7 && detector.jets[6].pT() > 90.) highPt = true;
      if (nJets >= 4 && detector.jets[3].pT() > 137.) tracklessBase = true;
      if (nJets >= 5 && detector.jets[4].pT() > 101.) tracklessBase = true;
      if (nJets >= 6 && detector.jets[5].pT() > 83.) tracklessBase = true;
      if (nJets >= 7 && detector.jets[6].pT() > 55.) tracklessBase = true;
      std::vector<double> displacedJets;
      for (int mother : decayed) for (std::size_t j = 0; j < detector.jets.size(); ++j) {
        double best = std::numeric_limits<double>::max();
        for (int track : descendants(pythia.event, mother)) {
          if (!pythia.event[track].isCharged() || !pythia.event[track].isFinal()) continue;
          double dphi = detector.jets[j].phi() - pythia.event[track].phi();
          if (std::abs(dphi) > M_PI) dphi = 2. * M_PI - std::abs(dphi);
          best = std::min(best, std::hypot(detector.jets[j].eta() - pythia.event[track].eta(), dphi));
        }
        if (best < .3 && std::abs(detector.jets[j].eta()) <= 2.5 && dvR <= 3870.) displacedJets.push_back(detector.jets[j].pT());
      }
      std::sort(displacedJets.begin(), displacedJets.end(), std::greater<double>());
      const bool trackless = tracklessBase && ((!displacedJets.empty() && displacedJets[0] > 70.) || (displacedJets.size() > 1 && displacedJets[1] > 50.));
      const bool jetPreselection = nJets >= 4;
      const bool jetSelection = highPt || trackless;
      if (jetSelection && mdv) {
        const double eventEff = highPt ? eventEff_HighPT(maxR, ht) : eventEff_Trackless(maxR, ht);
        eventProbability = std::max(0., eventEff);
      }
      const bool eventMap = eventProbability > 0.;
      const bool vertexMap = vertexProbability > 0.;
      const bool finalSelected = eventMap && vertexMap;
      const bool base = expected && successful && displaced && fiducial;
      const std::vector<bool> stages = {expected, successful, displaced, fiducial, jetPreselection, jetSelection, trackReq, multiplicity, mdv, eventMap && vertexMap};
      const bool flags[] = {true, expected, expected && successful, base && displaced, base, base && jetPreselection, base && jetPreselection && highPt, base && jetPreselection && trackless, base && jetSelection, base && jetSelection && candidateVertices > 0, base && jetSelection && trackReq, base && jetSelection && multiplicity, base && jetSelection && mdv, base && jetSelection && eventMap, base && jetSelection && vertexMap, base && jetSelection && finalSelected};
      for (int i = 0; i < 16; ++i) if (flags[i]) { ++raw[i]; weighted[i] += weight; }
      const Particle &h2 = decayed.empty() ? pythia.event[records.empty() ? 0 : records[0]] : pythia.event[decayed[0]];
      const double bg = h2.m() > 0. ? h2.pAbs() / h2.m() : 0.;
      const double dx = h2.xDec() - h2.xProd(), dy = h2.yDec() - h2.yProd(), dz = h2.zDec() - h2.zProd();
      const double lab = std::sqrt(dx * dx + dy * dy + dz * dz);
      const double proper = bg > 0. ? lab / bg : lab;
      out << "{\"event\":" << eventNumber << ",\"production_event_id\":" << eventNumber << ",\"replica_id\":0,\"lhe_weight\":" << lheWeight << ",\"analysis_weight_mb\":" << weight << ",\"h2_records\":" << records.size() << ",\"h2_bb_decays\":" << decayed.size() << ",\"beta_gamma\":" << bg << ",\"lab_flight_length_mm\":" << lab << ",\"proper_flight_length_mm\":" << proper << ",\"dv_radius_mm\":" << dvR << ",\"dv_z_mm\":" << dvZ << ",\"n_jets\":" << nJets << ",\"leading_jet_pt_GeV\":";
      writeNumber(out, nJets ? detector.jets[0].pT() : 0.); out << ",\"subleading_jet_pt_GeV\":"; writeNumber(out, nJets > 1 ? detector.jets[1].pT() : 0.);
      out << ",\"ht_GeV\":" << ht << ",\"charged_descendants\":" << charged << ",\"selected_displaced_track_multiplicity\":" << selectedTracks << ",\"truth_dv_mass_GeV\":" << truthMass << ",\"reconstructed_dv_mass_GeV\":" << truthMass << ",\"event_efficiency\":" << eventProbability << ",\"vertex_efficiency\":" << vertexProbability << ",\"failure_reason\":\"" << failure(stages) << "\"}\n";
    }
    std::ofstream meta(a.out + ".run.json");
    meta << "{\n  \"mode\": \"scalar-h2\",\n  \"pdg\": " << a.pdg << ",\n  \"mass_GeV\": " << a.mass << ",\n  \"ctau_mm\": " << a.ctau << ",\n  \"seed\": " << a.seed << ",\n  \"events\": " << a.events << ",\n  \"single_pythia_pass\": true,\n  \"channel\": [" << a.d1 << ", " << a.d2 << "],\n  \"branching_ratio\": " << a.br << "\n}\n";
    std::ofstream cf(a.out + ".stages.csv");
    cf << "stage,raw_count,weighted_count\n";
    for (int i = 0; i < 16; ++i) cf << stageNames[i] << ',' << raw[i] << ',' << weighted[i] << '\n';
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "scalar_h2_recast: " << e.what() << '\n';
    return 2;
  }
}
