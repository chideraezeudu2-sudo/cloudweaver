import React, { useState } from 'react';
import { Copy, Check, Terminal, ExternalLink, ArrowUpRight } from 'lucide-react';
import { InstallStep } from '../types';

const STEPS: InstallStep[] = [
  {
    number: 1,
    command: 'pip install cloudweaver',
    title: 'Install the CLI tool',
    description: 'Installs the lightweight Cloud Weaver client directly into your Python environment. No heavy daemon or background services required.',
  },
  {
    number: 2,
    command: 'cloudweaver login',
    title: 'Connect your account',
    description: 'Generates a secure browser session to authenticate your developer credentials and link your CLI session.',
  },
  {
    number: 3,
    command: 'cloudweaver add-funds 20',
    title: 'Add money to your wallet',
    description: 'Top up your prepaid balance using Stripe. No card details are ever stored locally or on third-party GPU marketplace nodes.',
  },
  {
    number: 4,
    command: 'cloudweaver run --gpu RTX_4090',
    title: 'Rent your first verified GPU',
    description: 'Finds the lowest priced node, benchmarks power and performance, and delivers an immediate SSH connection.',
  },
];

export const Install: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = (command: string, index: number) => {
    navigator.clipboard.writeText(command);
    setCopiedIndex(index);
    setTimeout(() => {
      setCopiedIndex(null);
    }, 2000);
  };

  return (
    <section id="install" className="w-full py-20 sm:py-24 md:py-28 px-6 sm:px-8 bg-[#ffffff]">
      <div className="max-w-[900px] mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-[640px] mx-auto mb-14 sm:mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] text-[13px] font-medium text-[#1f1f1f] tracking-[0.075em] uppercase mb-4">
            <Terminal className="w-3.5 h-3.5 text-[#594ff4]" />
            <span>Developer Quickstart</span>
          </div>
          <h2 className="text-[34px] sm:text-[44px] md:text-[50px] font-bold text-[#1f1f1f] tracking-[-0.03em] leading-[1.12]">
            Get started in under a minute
          </h2>
          <p className="mt-4 text-[16px] sm:text-[18px] text-[#5d5d5d] leading-[1.6]">
            Follow these four terminal commands to install the CLI, load your prepaid balance, and spin up your first verified compute node.
          </p>
        </div>

        {/* Vertical sequence of numbered steps */}
        <div className="space-y-6">
          {STEPS.map((step, idx) => {
            const isCopied = copiedIndex === idx;

            return (
              <div
                key={step.number}
                className="p-6 sm:p-7 rounded-[28px] bg-[#f6f6f6] border border-[#e7e7e7] hover:border-[#b0b0b0] transition-colors"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Step info */}
                  <div className="flex items-start gap-4">
                    <span className="w-8 h-8 rounded-full bg-white border border-[#e7e7e7] text-[#1f1f1f] font-mono text-[14px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {step.number}
                    </span>
                    <div>
                      <h3 className="text-[17px] font-bold text-[#1f1f1f]">
                        {step.title}
                      </h3>
                      <p className="text-[14px] text-[#5d5d5d] mt-1 leading-[1.5]">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Command box with copy button */}
                <div className="mt-4 flex items-center justify-between bg-[#1f1f1f] text-[#f6f6f6] rounded-xl px-4 py-3 font-mono text-[13.5px] sm:text-[14px] border border-[#333333]">
                  <div className="flex items-center gap-2 overflow-x-auto">
                    <span className="text-[#594ff4] font-bold select-none">$</span>
                    <span className="text-[#f6f6f6] select-all">{step.command}</span>
                  </div>

                  <button
                    onClick={() => handleCopy(step.command, idx)}
                    className="ml-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-sans font-medium bg-[#2b2b2b] hover:bg-[#383838] text-white transition-colors shrink-0 cursor-pointer"
                    title="Copy command"
                    aria-label={`Copy ${step.command}`}
                  >
                    {isCopied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-[#27c93f]" />
                        <span className="text-[#27c93f]">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5 text-[#b0b0b0]" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Button below steps: View full documentation */}
        <div className="mt-12 text-center">
          <a
            href="https://github.com/chideraezeudu2-sudo/cloudweaver#readme"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-[15px] font-medium text-[#1f1f1f] border border-[#e7e7e7] hover:border-[#594ff4] hover:text-[#594ff4] bg-white transition-all cursor-pointer shadow-sm"
            id="install-view-docs-button"
          >
            <span>View full documentation</span>
            <ArrowUpRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    </section>
  );
};
