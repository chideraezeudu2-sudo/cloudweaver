import React from 'react';
import { ArrowRight, Terminal } from 'lucide-react';

interface FinalCTAProps {
  onScrollTo: (id: string) => void;
}

export const FinalCTA: React.FC<FinalCTAProps> = ({ onScrollTo }) => {
  return (
    <section id="cta" className="w-full py-20 sm:py-24 md:py-28 px-6 sm:px-8 bg-[#f6f6f6] border-t border-[#e7e7e7]">
      <div className="max-w-[1000px] mx-auto text-center flex flex-col items-center">
        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white border border-[#e7e7e7] text-[13px] font-medium text-[#1f1f1f] tracking-[0.05em] uppercase mb-6">
          <Terminal className="w-3.5 h-3.5 text-[#594ff4]" />
          <span>Ready in 60 seconds</span>
        </div>

        {/* Headline */}
        <h2 className="text-[36px] sm:text-[48px] md:text-[56px] font-bold text-[#1f1f1f] tracking-[-0.03em] leading-[1.08] max-w-[800px]">
          Stop paying for GPUs that aren&apos;t there
        </h2>

        {/* Subtext */}
        <p className="mt-5 text-[17px] sm:text-[19px] text-[#5d5d5d] max-w-[620px] leading-[1.55]">
          Query live market inventory, verify real hardware performance, and connect to guaranteed compute directly from your terminal.
        </p>

        {/* Single Primary Action Button */}
        <div className="mt-8 sm:mt-10">
          <button
            onClick={() => onScrollTo('install')}
            className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-[16px] font-medium text-white bg-[#594ff4] hover:bg-[#4d42e6] active:scale-[0.98] transition-all duration-150 cursor-pointer shadow-none"
            id="final-cta-get-started"
          >
            <span>Get Started</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
};
