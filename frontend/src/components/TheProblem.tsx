import React from 'react';
import { Ghost, Cpu, AlertTriangle, ShieldCheck } from 'lucide-react';

export const TheProblem: React.FC = () => {
  return (
    <section id="problem" className="w-full py-16 sm:py-20 md:py-24 px-6 sm:px-8 border-t border-[#f6f6f6]">
      <div className="max-w-[1100px] mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-[760px] mx-auto mb-12 sm:mb-16">
          <div className="inline-flex items-center gap-1.5 text-[13px] font-medium tracking-[0.075em] uppercase text-[#888888] mb-3">
            <AlertTriangle className="w-4 h-4 text-[#594ff4]" />
            <span>Marketplace Reality</span>
          </div>
          <h2 className="text-[32px] sm:text-[42px] md:text-[48px] font-bold text-[#1f1f1f] tracking-[-0.025em] leading-[1.15]">
            GPU marketplaces lie to you
          </h2>
          <p className="mt-4 text-[16px] sm:text-[17px] text-[#5d5d5d] leading-[1.6]">
            Aggregators and community marketplaces look cheap on the surface, but raw price-comparison tables hide two persistent failure modes that cost engineers hours of lost time and wasted balance.
          </p>
        </div>

        {/* Two side-by-side explanation blocks */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
          {/* Block 1: Ghost Inventory */}
          <div
            className="p-8 sm:p-10 rounded-[36px] bg-[#f6f6f6] border border-[#e7e7e7]/80 flex flex-col justify-between hover:border-[#b0b0b0] transition-colors"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-white border border-[#e7e7e7] flex items-center justify-center text-[#594ff4] mb-6">
                <Ghost className="w-6 h-6 stroke-[1.75]" />
              </div>
              <h3 className="text-[22px] sm:text-[24px] font-bold text-[#1f1f1f] tracking-[-0.015em] mb-3">
                Ghost inventory.
              </h3>
              <p className="text-[15px] sm:text-[16px] text-[#5d5d5d] leading-[1.65]">
                GPU listings across decentralized marketplaces are frequently unavailable the moment you attempt to rent them. The attractive spot rate you see on a dashboard isn&apos;t the machine you actually get: by the time you submit your request, another script has taken it, the host node dropped offline, or the listing was phantom data left in a stale index.
              </p>
            </div>

            <div className="mt-8 pt-4 border-t border-[#e7e7e7] text-[13px] text-[#888888] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#ff5f56]"></span>
              <span>Result: failed spin-up scripts, broken CI/CD runs, manual retries.</span>
            </div>
          </div>

          {/* Block 2: Misrepresented Hardware */}
          <div
            className="p-8 sm:p-10 rounded-[36px] bg-[#f6f6f6] border border-[#e7e7e7]/80 flex flex-col justify-between hover:border-[#b0b0b0] transition-colors"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-white border border-[#e7e7e7] flex items-center justify-center text-[#594ff4] mb-6">
                <Cpu className="w-6 h-6 stroke-[1.75]" />
              </div>
              <h3 className="text-[22px] sm:text-[24px] font-bold text-[#1f1f1f] tracking-[-0.015em] mb-3">
                Misrepresented hardware.
              </h3>
              <p className="text-[15px] sm:text-[16px] text-[#5d5d5d] leading-[1.65]">
                A GPU can be the right model on paper but secretly underpowered. Unmonitored hosts frequently clamp power targets (e.g. running an RTX 4090 capped at 220W instead of 450W), choke PCIe lane bandwidth, or allow severe thermal throttling — delivering a fraction of rated compute with no warning until your training run crawls.
              </p>
            </div>

            <div className="mt-8 pt-4 border-t border-[#e7e7e7] text-[13px] text-[#888888] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#ff5f56]"></span>
              <span>Result: paying for premium silicone while getting half the throughput.</span>
            </div>
          </div>
        </div>

        {/* Closing line under both blocks that pivots into solution */}
        <div className="mt-10 sm:mt-12 text-center p-6 sm:p-8 rounded-[24px] bg-[#ffffff] border border-[#e7e7e7] max-w-[800px] mx-auto shadow-sm">
          <div className="flex items-center justify-center gap-2 text-[#594ff4] mb-2">
            <ShieldCheck className="w-5 h-5" />
            <span className="text-[13px] font-semibold uppercase tracking-[0.05em]">Guaranteed Baseline</span>
          </div>
          <p className="text-[18px] sm:text-[20px] font-bold text-[#1f1f1f] tracking-[-0.015em]">
            Cloud Weaver checks for both, before you&apos;re ever charged.
          </p>
        </div>
      </div>
    </section>
  );
};
