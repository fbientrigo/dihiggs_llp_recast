// R8 supplementary geometry/kinematic driver.
//
// Reads the SAME .cmnd card used by the real recast binary
// (results/upstream_build_patched/analysis/recast_2301_13866), via
// pythia.readFile(), so ISR/FSR/MPI/hadronization/Tune:pp/seed/tau0 are
// identical to the analysis run by construction, not by hand-copying
// settings. Dumps per-LLP Rxy/L3D/tau geometry and per-event jet
// multiplicity/leading-jet pT for the Phase 4/5 distribution comparisons.
//
// Jet clustering (kt_algorithm, R=0.4, E_scheme, Best strategy, inclusive
// pT > 20 GeV) matches ToyDetector::jetDef in the frozen upstream
// Simpler_ToyDetector.cc. Final visible particles are used directly as
// FastJet input WITHOUT the analysis's isolated-lepton removal: this is a
// supplementary kinematic cross-check, not a reimplementation of the
// analysis's own signal-region jet collection (Phase 2 forbids touching
// that logic), so jet counts/leading-pT here may differ slightly from what
// the real recast binary uses internally for selection.
//
// The Recast:llpPdgIds / Recast:llpTau0 settings in the card are meaningful
// only to the patched analysis binary; here they are read directly (not via
// the Pythia settings database, since this driver does not carry the
// upstream patch) to identify which PDG to track and to confirm the
// post-init tau0 the card requests.

#include "Pythia8/Pythia.h"
#include "fastjet/ClusterSequence.hh"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace Pythia8;

static double parseCardDouble(const std::string& cardPath, const std::string& key) {
  std::ifstream fin(cardPath);
  std::string line;
  double value = -1.0;
  while (std::getline(fin, line)) {
    auto hash = line.find('!');
    if (hash != std::string::npos) line = line.substr(0, hash);
    auto eq = line.find('=');
    if (eq == std::string::npos) continue;
    std::string k = line.substr(0, eq);
    // trim
    k.erase(0, k.find_first_not_of(" \t"));
    k.erase(k.find_last_not_of(" \t") + 1);
    if (k == key) value = std::stod(line.substr(eq + 1));
  }
  return value;
}

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: r8_geometry_driver card.cmnd expected_events out.csv\n";
    return 2;
  }
  const std::string cardPath = argv[1];
  const long long expectedEvents = std::stoll(argv[2]);
  const std::string outCsv = argv[3];

  const double llpTau0 = parseCardDouble(cardPath, "Recast:llpTau0");
  if (llpTau0 <= 0.0) {
    std::cerr << "could not read a positive Recast:llpTau0 from " << cardPath << "\n";
    return 2;
  }
  const int llpPdg = 35; // matches Recast:llpPdgIds = {35} in the R8/R7 cards

  Pythia pythia;
  // The cards carry Recast:llpPdgIds/Recast:llpTau0/LHEFInputs:nSubruns,
  // which are only registered as known settings by the patched analysis
  // binary (recast_2301_13866.cc); register the same keys here so a plain
  // Pythia instance accepts the unmodified card instead of aborting on an
  // unrecognized settings line. llpPdgIds/llpTau0 values are re-read
  // directly from the card text above (parseCardDouble) rather than via
  // these settings, since only nSubruns is needed for LHEF handling here.
  pythia.settings.addMode("LHEFInputs:nSubruns", 0, true, false, 0, 100);
  pythia.settings.addMVec("Recast:llpPdgIds", {1000022, 1000023, 1000024}, false, false, 0, 0);
  pythia.settings.addParm("Recast:llpTau0", -1., false, false, 0., 0.);
  pythia.readFile(cardPath);
  // Mirrors the analysis binary: settings after "Main:subrun = N" are
  // subrun-scoped (this is how Beams:LHEF reaches Pythia at all) and are
  // only applied by a second readFile call naming that subrun index.
  pythia.readFile(cardPath, 0);
  if (!pythia.init()) return 3;
  pythia.particleData.tauCalc(llpPdg, false);
  pythia.particleData.tau0(llpPdg, llpTau0);
  std::cout << "R8_GEOMETRY_SETTINGS: pdg=" << llpPdg
            << " tau0=" << std::setprecision(16) << pythia.particleData.tau0(llpPdg)
            << " tauCalc=" << pythia.particleData.tauCalc(llpPdg) << "\n";

  fastjet::JetDefinition jetDef(fastjet::kt_algorithm, 0.4, fastjet::E_scheme, fastjet::Best);

  std::ofstream csv(outCsv);
  csv << "event,llp_index,tau_generated_mm,Rxy_mm,L3D_mm,n_jets_pt20,leading_jet_pt_GeV,"
         "daughter1_id,daughter2_id\n";

  long long nEvents = 0, nLLP = 0, nBBbarDecays = 0;
  while (nEvents < expectedEvents) {
    if (!pythia.next()) {
      if (pythia.info.atEndOfFile()) {
        std::cerr << "truncated input: EOF after " << nEvents << " of " << expectedEvents << "\n";
        return 4;
      }
      std::cerr << "generation failed before reaching " << expectedEvents << " events (at " << nEvents << ")\n";
      return 5;
    }
    ++nEvents;

    std::vector<fastjet::PseudoJet> fjInputs;
    for (int i = 0; i < pythia.event.size(); ++i) {
      const Particle& p = pythia.event[i];
      if (p.isFinal() && p.isVisible())
        fjInputs.emplace_back(p.px(), p.py(), p.pz(), p.e());
    }
    fastjet::ClusterSequence clustSeq(fjInputs, jetDef);
    std::vector<fastjet::PseudoJet> jets = sorted_by_pt(clustSeq.inclusive_jets(20.0));
    const long long nJets = static_cast<long long>(jets.size());
    const double leadingPt = jets.empty() ? 0.0 : jets.front().pt();

    for (int i = 0; i < pythia.event.size(); ++i) {
      const Particle& p = pythia.event[i];
      if (std::abs(p.id()) != llpPdg) continue;
      if (p.daughterList().size() != 2) continue;
      ++nLLP;
      const double dx = p.xDec() - p.xProd();
      const double dy = p.yDec() - p.yProd();
      const double dz = p.zDec() - p.zProd();
      const double rxy = std::hypot(dx, dy);
      const double l3d = std::sqrt(dx * dx + dy * dy + dz * dz);
      const auto daughters = p.daughterList();
      const int d1 = pythia.event[daughters[0]].id();
      const int d2 = pythia.event[daughters[1]].id();
      if ((d1 == 5 && d2 == -5) || (d1 == -5 && d2 == 5)) ++nBBbarDecays;
      csv << nEvents << ',' << i << ',' << std::setprecision(16) << p.tau() << ',' << rxy << ',' << l3d
          << ',' << nJets << ',' << leadingPt << ',' << d1 << ',' << d2 << '\n';
    }
  }
  const bool extraEventAvailable = pythia.next();
  if (extraEventAvailable || !pythia.info.atEndOfFile()) {
    std::cerr << "input does not contain exactly " << expectedEvents << " events\n";
    return 6;
  }
  if (nEvents != expectedEvents || nLLP != 2 * expectedEvents || nBBbarDecays != 2 * expectedEvents) {
    std::cerr << "count mismatch: events=" << nEvents << " llp=" << nLLP
               << " bbbar_decays=" << nBBbarDecays << "\n";
    return 7;
  }
  std::cout << "R8_GEOMETRY_DRIVER: events=" << nEvents << " llp_records=" << nLLP
            << " bbbar_decays=" << nBBbarDecays << " status=PASS\n";
  return 0;
}
