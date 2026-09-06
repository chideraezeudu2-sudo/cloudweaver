import React, { useState } from 'react';
import { Check, Copy, Wallet, ShieldCheck, ArrowRight } from 'lucide-react';
import { PricingOption } from '../types';

interface PricingProps {
  onScrollTo: (id: string) => void;
}

const PRICING_OPTIONS: PricingOption[] = [
  { amount: 5, label: '$5', estHours4090: '~13 hrs', estHoursA100: '~4.3 hrs' },
  { amount: 10, label: '$10', estHours4090: '~26 hrs', estHoursA100: '~8.7 hrs' },
  { amount: 20, label: '$20', estHours4090: '~52 hrs', estHoursA100: '~17.4 hrs', popular: true },
  { amount: 50, label: '$50', estHours4090: '~131 hrs', estHoursA100: '~43.5 hrs' },
  { amount: 100, label: '$100', estHours4090: '~263 hrs', estHoursA100: '~87 hrs' },
];

export const Pricing: React.FC<PricingProps> = ({ onScrollTo }) => {
  const [selectedAmount, setSelectedAmount] = useState<number>(20);
  const [copied, setCopied] = useState(false);

  const selectedOpt = PRICING_OPTIONS.find((opt) => opt.amount === selectedAmount) || PRICING_OPTIONS[2];

  const handleCopyCommand = () => {
    navigator.clipboard.writeText(`cloudweaver add-funds ${selectedAmount}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="pricing" className="w-full py-20 sm:py-24 md:py-28 px-6 sm:px-8 bg-[#f6f6f6] border-t border-[#e7e7e7]">
      <div className="max-w-[1100px] mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-[760px] mx-auto mb-14 sm:mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#e7e7e7] text-[13px] font-medium text-[#1f1f1f] tracking-[0.075em] uppercase mb-4">
            <Wallet className="w-3.5 h-3.5 text-[#594ff4]" />
            <span>Transparent Compute</span>
          </div>
          <h2 className="text-[34px] sm:text-[44px] md:text-[50px] font-bold text-[#1f1f1f] tracking-[-0.03em] leading-[1.12]">
            Pricing
          </h2>
          <p className="mt-4 text-[16px] sm:text-[18px] text-[#5d5d5d] leading-[1.6]">
            Pay-as-you-go from a prepaid wallet, billed per second of actual usage, no subscription, no minimum commitment.
          </p>
        </div>

        {/* Five Options displayed side-by-side / equal weight choices */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3.5 sm:gap-4 mb-10">
          {PRICING_OPTIONS.map((opt) => {
            const isSelected = selectedAmount === opt.amount;
            return (
              <button
                key={opt.amount}
                onClick={() => setSelectedAmount(opt.amount)}
                className={`p-5 sm:p-6 rounded-[24px] text-center transition-all duration-150 border flex flex-col items-center justify-between cursor-pointer ${
                  isSelected
                    ? 'bg-white border-[#594ff4] shadow-md ring-2 ring-[#594ff4]/20'
                    : 'bg-white border-[#e7e7e7] hover:border-[#b0b0b0]'
                }`}
              >
                <div className="w-full">
                  <div className="text-[28px] sm:text-[32px] font-bold text-[#1f1f1f] tracking-tight">
                    {opt.label}
                  </div>
                  <div className="text-[12px] font-medium text-[#888888] uppercase tracking-wider mt-1">
                    Prepaid Credit
                  </div>
                </div>

                <div className="w-full mt-4 pt-3 border-t border-[#f0f0f0] text-[12px] text-[#5d5d5d] space-y-1">
                  <div>4090: <span className="font-semibold text-[#1f1f1f]">{opt.estHours4090}</span></div>
                  <div>A100: <span className="font-semibold text-[#1f1f1f]">{opt.estHoursA100}</span></div>
                </div>

                <div className="mt-4">
                  <span
                    className={`inline-block w-4 h-4 rounded-full border flex items-center justify-center transition-colors ${
                      isSelected
                        ? 'bg-[#594ff4] border-[#594ff4]'
                        : 'border-[#b0b0b0]'
                    }`}
                  >
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white"></span>}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Interactive CLI Action Box for selected credit */}
        <div className="p-6 sm:p-7 rounded-[28px] bg-white border border-[#e7e7e7] max-w-[760px] mx-auto mb-12 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <div className="text-[13px] text-[#888888] font-medium uppercase tracking-wider">CLI Wallet Command</div>
            <div className="text-[15px] text-[#1f1f1f] font-semibold mt-0.5 font-mono">
              cloudweaver add-funds {selectedOpt.amount}
            </div>
            <div className="text-[13px] text-[#5d5d5d] mt-1">
              Provides approximately <span className="text-[#1f1f1f] font-medium">{selectedOpt.estHours4090}</span> on verified RTX 4090 compute.
            </div>
          </div>

          <button
            onClick={handleCopyCommand}
            className="w-full sm:w-auto px-5 py-2.5 rounded-full text-[14px] font-medium text-[#1f1f1f] bg-[#f6f6f6] hover:bg-[#e7e7e7] transition-colors flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-[#594ff4]" />
                <span className="text-[#594ff4]">Copied to clipboard</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 text-[#5d5d5d]" />
                <span>Copy Command</span>
              </>
            )}
          </button>
        </div>

        {/* Short List Underneath: What you're never charged for */}
        <div className="max-w-[760px] mx-auto p-7 sm:p-8 rounded-[32px] bg-white border border-[#e7e7e7]">
          <div className="flex items-center gap-2 text-[#1f1f1f] font-bold text-[18px] mb-4">
            <ShieldCheck className="w-5 h-5 text-[#594ff4]" />
            <span>What you&apos;re never charged for</span>
          </div>

          <div className="grid grid-cols-1 gap-3.5">
            <div className="flex items-start gap-3 text-[15px] text-[#5d5d5d] leading-[1.5]">
              <div className="w-5 h-5 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-[#594ff4]" />
              </div>
              <span>
                <strong className="text-[#1f1f1f] font-semibold">Failed reservation attempts:</strong> if a marketplace listing was phantom ghost inventory or taken before reservation locked, it costs you $0.
              </span>
            </div>

            <div className="flex items-start gap-3 text-[15px] text-[#5d5d5d] leading-[1.5]">
              <div className="w-5 h-5 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-[#594ff4]" />
              </div>
              <span>
                <strong className="text-[#1f1f1f] font-semibold">GPUs that fail the hardware check:</strong> if a host has capped the power limit, thermal-throttled the card, or restricted PCIe lanes, the diagnostic test rejects it with no charge.
              </span>
            </div>

            <div className="flex items-start gap-3 text-[15px] text-[#5d5d5d] leading-[1.5]">
              <div className="w-5 h-5 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-[#594ff4]" />
              </div>
              <span>
                <strong className="text-[#1f1f1f] font-semibold">Compute time after a provider reclaims an interruptible instance:</strong> metering halts the exact second spot reclamation is detected.
              </span>
            </div>
          </div>

          {/* Single Button at the bottom of pricing section: "Add funds" */}
          <div className="mt-8 pt-6 border-t border-[#e7e7e7] flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-[14px] text-[#888888]">
              Funds never expire. Unused balances are refundable on request.
            </span>
            <button
              onClick={() => onScrollTo('install')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full text-[15px] font-medium text-white bg-[#594ff4] hover:bg-[#4d42e6] active:scale-[0.98] transition-all duration-150 cursor-pointer"
              id="pricing-add-funds-button"
            >
              <span>Add funds</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
