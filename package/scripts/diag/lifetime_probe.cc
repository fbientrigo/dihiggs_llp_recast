// Mission 01B — LLP lifetime propagation probe.
//
// TOY_LIFETIME_PLUMBING_TEST. Synthetic LHE input: this measures plumbing
// (does a proper lifetime reach the decay vertex?), never physics.
//
// Three execution paths, selected by argv[2]:
//
//   baseline    single pythia.next(); no repair. Reproduces the Mission 01 failure.
//   setlifetime single pythia.next(); LesHouches:setLifetime = 2 forced before init.
//   staged      HadronLevel:all = off -> init -> isResonance(pdg,false) +
//               mayDecay(pdg,true) -> per event: next(), sample tau on final
//               LLPs, then forceHadronLevel().
//
// Emits a per-LLP CSV (first N events, one row per LLP per phase) and a JSON
// summary over the full sample.
#include "Pythia8/Pythia.h"
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

using namespace Pythia8;

namespace {

const int LLP_PDG = 9900035;
int csvEvents() { const char* e = getenv("PROBE_CSV_EVENTS"); return e ? atoi(e) : 10; }
const int CSV_EVENTS_DEFAULT = 10;

struct Stat {
  std::vector<double> v;
  void add(double x) { v.push_back(x); }
  double mean() const {
    if (v.empty()) return 0.;
    double s = 0.; for (double x : v) s += x; return s / v.size();
  }
  double stddev() const {
    if (v.size() < 2) return 0.;
    double m = mean(), s = 0.;
    for (double x : v) s += (x - m) * (x - m);
    return std::sqrt(s / (v.size() - 1));
  }
  size_t n() const { return v.size(); }
};

// True if no daughter of p is itself an LLP, i.e. p is the copy that really decays.
bool isTerminalLlp(const Event& ev, int i) {
  for (int d : ev[i].daughterList())
    if (ev[d].idAbs() == LLP_PDG) return false;
  return true;
}

void writeRow(std::ostream& os, int event, const std::string& phase, const Event& ev,
              int i, const ParticleData& pd) {
  const Particle& p = ev[i];
  double dx = p.xDec() - p.xProd();
  double dy = p.yDec() - p.yProd();
  double dz = p.zDec() - p.zProd();
  double L3D = std::sqrt(dx * dx + dy * dy + dz * dz);
  double Rxy = std::sqrt(p.xDec() * p.xDec() + p.yDec() * p.yDec());
  double betaGamma = (p.m() > 0.) ? p.pAbs() / p.m() : 0.;
  os << event << ',' << phase << ',' << i << ',' << p.id() << ',' << p.status() << ','
     << p.mother1() << ',' << p.mother2() << ',' << p.daughter1() << ',' << p.daughter2() << ','
     << p.m() << ',' << p.e() << ',' << p.pAbs() << ',' << betaGamma << ','
     << p.tau0() << ',' << p.tau() << ','
     << p.xProd() << ',' << p.yProd() << ',' << p.zProd() << ','
     << p.xDec() << ',' << p.yDec() << ',' << p.zDec() << ','
     << L3D << ',' << Rxy << ','
     << (pd.isResonance(LLP_PDG) ? 1 : 0) << ',' << (pd.mayDecay(LLP_PDG) ? 1 : 0) << '\n';
}

}  // namespace

int main(int argc, char* argv[]) {
  if (argc < 3) {
    std::cerr << "usage: lifetime_probe <cmnd> <baseline|setlifetime|staged> "
                 "[csvOut] [jsonOut]\n";
    return 2;
  }
  const std::string cmnd = argv[1];
  const std::string mode = argv[2];
  const std::string csvOut  = (argc >= 4) ? argv[3] : "";
  const std::string jsonOut = (argc >= 5) ? argv[4] : "";
  const bool staged = (mode == "staged");

  if (mode != "baseline" && mode != "setlifetime" && mode != "staged") {
    std::cerr << "unknown mode: " << mode << "\n";
    return 2;
  }

  Pythia pythia;
  pythia.settings.addMode("LHEFInputs:nSubruns", 0, true, false, 0, 100);
  pythia.readFile(cmnd);
  pythia.readFile(cmnd, 0);

  // --- pre-init configuration -------------------------------------------------
  if (mode == "setlifetime")
    pythia.settings.mode("LesHouches:setLifetime", 2);
  if (staged)
    pythia.settings.flag("HadronLevel:all", false);

  // Pre-init particle-data state (particle not yet created by the SLHA reader).
  const bool knownPreInit = (pythia.particleData.findParticle(LLP_PDG) != nullptr);

  pythia.init();

  // --- post-init repair -------------------------------------------------------
  if (staged) {
    pythia.particleData.isResonance(LLP_PDG, false);
    pythia.particleData.mayDecay(LLP_PDG, true);
  }

  ParticleDataEntryPtr pd = pythia.particleData.findParticle(LLP_PDG);
  if (pd == nullptr) { std::cerr << "[FAIL] PDG " << LLP_PDG << " unknown after init\n"; return 3; }

  std::cout << "=== mode: " << mode << " ===\n"
            << "known_pre_init  = " << (knownPreInit ? "true" : "false") << "\n"
            << "m0              = " << pd->m0() << "\n"
            << "mWidth          = " << pd->mWidth() << "\n"
            << "tau0            = " << pd->tau0() << " mm\n"
            << "isResonance     = " << pd->isResonance() << "\n"
            << "mayDecay        = " << pd->mayDecay() << "\n"
            << "decay channels  = " << pd->sizeChannels() << "\n"
            << "setLifetime     = " << pythia.settings.mode("LesHouches:setLifetime") << "\n";

  std::ofstream csv;
  if (!csvOut.empty()) {
    csv.open(csvOut);
    csv << std::setprecision(8);
    csv << "event,phase,index,pdg,status,mother1,mother2,daughter1,daughter2,mass,energy,"
           "pAbs,betaGamma,tau0,tau,xProd,yProd,zProd,xDec,yDec,zDec,L3D,Rxy,"
           "isResonance,mayDecay\n";
  }

  Stat sTau, sL3D, sRxy, sBg;
  int nEvents = pythia.mode("Main:numberOfEvents");
  int nProcessed = 0, nRxyGt4 = 0, nEventsWithFinalPair = 0, nStatusMinus22 = 0;
  int nDaughtersDisplaced = 0, nTerminal = 0;

  for (int iEvent = 0; iEvent < nEvents; ++iEvent) {
    if (!pythia.next()) {
      if (pythia.info.atEndOfFile()) break;
      continue;
    }

    if (staged) {
      // Locate final, undecayed LLPs and give each a sampled proper lifetime.
      std::vector<int> finalLlp;
      for (int i = 0; i < pythia.event.size(); ++i)
        if (pythia.event[i].idAbs() == LLP_PDG && pythia.event[i].isFinal())
          finalLlp.push_back(i);

      if (finalLlp.size() == 2) nEventsWithFinalPair++;

      for (int i : finalLlp)
        pythia.event[i].tau(pythia.event[i].tau0() * pythia.rndm.exp());

      if (iEvent < csvEvents() && csv.is_open())
        for (int i : finalLlp) writeRow(csv, iEvent, "pre_hadron", pythia.event, i,
                                        pythia.particleData);

      if (!pythia.forceHadronLevel()) {
        std::cerr << "[WARN] forceHadronLevel failed on event " << iEvent << "\n";
        continue;
      }
    }

    nProcessed++;
    const std::string phase = staged ? "post_hadron" : "single_call";

    for (int i = 0; i < pythia.event.size(); ++i) {
      Particle& p = pythia.event[i];
      if (p.idAbs() != LLP_PDG) continue;
      if (!isTerminalLlp(pythia.event, i)) continue;
      nTerminal++;
      if (p.status() == -22) nStatusMinus22++;

      double dx = p.xDec() - p.xProd(), dy = p.yDec() - p.yProd(), dz = p.zDec() - p.zProd();
      double L3D = std::sqrt(dx * dx + dy * dy + dz * dz);
      double Rxy = std::sqrt(p.xDec() * p.xDec() + p.yDec() * p.yDec());
      sTau.add(p.tau()); sL3D.add(L3D); sRxy.add(Rxy);
      if (p.m() > 0.) sBg.add(p.pAbs() / p.m());
      if (Rxy > 4.) nRxyGt4++;

      // Did the daughters actually inherit the displaced production vertex?
      for (int d : p.daughterList()) {
        double dr = std::sqrt(pythia.event[d].xProd() * pythia.event[d].xProd() +
                              pythia.event[d].yProd() * pythia.event[d].yProd());
        if (dr > 1e-9) { nDaughtersDisplaced++; break; }
      }

      if (iEvent < csvEvents() && csv.is_open())
        writeRow(csv, iEvent, phase, pythia.event, i, pythia.particleData);
    }
  }
  if (csv.is_open()) csv.close();

  std::cout << "\n=== SUMMARY (" << mode << ") ===\n"
            << "events processed        : " << nProcessed << "\n"
            << "terminal LLPs           : " << nTerminal << "\n"
            << "events with 2 final LLPs: " << nEventsWithFinalPair << (staged ? "" : " (staged only)") << "\n"
            << "terminal LLPs status -22: " << nStatusMinus22 << "\n"
            << "LLPs w/ displaced daus  : " << nDaughtersDisplaced << "\n"
            << "LLPs with Rxy > 4mm     : " << nRxyGt4 << "\n"
            << "mean betaGamma          : " << sBg.mean() << "\n"
            << "mean tau                : " << sTau.mean() << " +- " << sTau.stddev() << " mm\n"
            << "mean L3D                : " << sL3D.mean() << " +- " << sL3D.stddev() << " mm\n"
            << "mean Rxy                : " << sRxy.mean() << " +- " << sRxy.stddev() << " mm\n";

  if (!jsonOut.empty()) {
    std::ofstream js(jsonOut);
    js << std::setprecision(8);
    js << "{\n"
       << "  \"label\": \"TOY_LIFETIME_PLUMBING_TEST\",\n"
       << "  \"mode\": \"" << mode << "\",\n"
       << "  \"llp_pdg\": " << LLP_PDG << ",\n"
       << "  \"particle_data\": {\n"
       << "    \"known_pre_init\": " << (knownPreInit ? "true" : "false") << ",\n"
       << "    \"m0_gev\": " << pd->m0() << ",\n"
       << "    \"mWidth_gev\": " << pd->mWidth() << ",\n"
       << "    \"tau0_mm\": " << pd->tau0() << ",\n"
       << "    \"isResonance\": " << (pd->isResonance() ? "true" : "false") << ",\n"
       << "    \"mayDecay\": " << (pd->mayDecay() ? "true" : "false") << ",\n"
       << "    \"n_decay_channels\": " << pd->sizeChannels() << ",\n"
       << "    \"les_houches_set_lifetime\": " << pythia.settings.mode("LesHouches:setLifetime") << "\n"
       << "  },\n"
       << "  \"counts\": {\n"
       << "    \"events_processed\": " << nProcessed << ",\n"
       << "    \"terminal_llps\": " << nTerminal << ",\n"
       << "    \"events_with_two_final_llps\": " << nEventsWithFinalPair << ",\n"
       << "    \"terminal_llps_status_minus22\": " << nStatusMinus22 << ",\n"
       << "    \"llps_with_displaced_daughters\": " << nDaughtersDisplaced << ",\n"
       << "    \"llps_Rxy_gt_4mm\": " << nRxyGt4 << "\n"
       << "  },\n"
       << "  \"distributions\": {\n"
       << "    \"betaGamma_mean\": " << sBg.mean() << ",\n"
       << "    \"tau_mean_mm\": " << sTau.mean() << ", \"tau_std_mm\": " << sTau.stddev() << ",\n"
       << "    \"L3D_mean_mm\": " << sL3D.mean() << ", \"L3D_std_mm\": " << sL3D.stddev() << ",\n"
       << "    \"Rxy_mean_mm\": " << sRxy.mean() << ", \"Rxy_std_mm\": " << sRxy.stddev() << ",\n"
       << "    \"n\": " << sL3D.n() << "\n"
       << "  }\n"
       << "}\n";
  }
  return 0;
}
