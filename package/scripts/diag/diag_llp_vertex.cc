#include "Pythia8/Pythia.h"
#include <iostream>
using namespace Pythia8;
int main(int argc, char* argv[]) {
  Pythia pythia;
  pythia.settings.addMode("LHEFInputs:nSubruns", 0, true, false, 0, 100);
  pythia.readFile(argv[1]);
  pythia.readFile(argv[1], 0);
  pythia.init();
  ParticleDataEntryPtr pd = pythia.particleData.findParticle(9900035);
  std::cout << "\n=== PARTICLE DATA 9900035 ===\n"
            << "  m0          = " << pd->m0() << "\n"
            << "  mWidth      = " << pd->mWidth() << "\n"
            << "  tau0        = " << pd->tau0() << " mm\n"
            << "  mayDecay    = " << pd->mayDecay() << "\n"
            << "  isResonance = " << pd->isResonance() << "   <-- prompt if 1\n"
            << "  doExternalDecay = " << pd->doExternalDecay() << "\n";
  int nTerm = 0, nRgt4 = 0; double sumR = 0.;
  for (int i = 0; i < pythia.mode("Main:numberOfEvents"); ++i) {
    if (!pythia.next()) continue;
    for (int j = 0; j < pythia.event.size(); ++j) {
      Particle& p = pythia.event[j];
      if (p.idAbs() != 9900035) continue;
      // terminal copy = no daughter is itself an LLP
      bool terminal = true;
      for (int d : p.daughterList())
        if (pythia.event[d].idAbs() == 9900035) terminal = false;
      if (!terminal) continue;
      nTerm++;
      double r = sqrt(pow(p.xDec(),2) + pow(p.yDec(),2));
      sumR += r; if (r > 4.) nRgt4++;
      if (nTerm <= 6) {
        std::cout << "[TERMINAL LLP] status=" << p.status() << " tau=" << p.tau()
                  << " rDec=" << r << " daughters:";
        for (int d : p.daughterList()) std::cout << " " << pythia.event[d].id();
        std::cout << std::endl;
      }
    }
  }
  std::cout << "\n=== TERMINAL LLP SUMMARY ===\n"
            << "  terminal LLPs   : " << nTerm << "\n"
            << "  with rDec > 4mm : " << nRgt4 << "\n"
            << "  mean rDec       : " << (nTerm? sumR/nTerm : 0) << " mm\n";
  return 0;
}
