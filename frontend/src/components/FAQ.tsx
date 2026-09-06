import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';
import { FAQItem } from '../types';

const FAQS: FAQItem[] = [
  {
    id: 'providers',
    question: 'Which GPU providers do you support?',
    answer:
      'We currently aggregate and verify capacity from Vast.ai and RunPod. Additional cloud marketplaces and independent GPU clusters are scheduled for integration as our verification network expands.',
  },
  {
    id: 'interruptions',
    question: 'What happens if my job gets interrupted?',
    answer:
      'Cloud Weaver continuously monitors heartbeat signals from the host machine. If a spot or interruptible instance is reclaimed by the provider, our broker detects the eviction instantly and halts metering in that exact second. You never pay for unrendered compute.',
  },
  {
    id: 'payments',
    question: 'Do you store my payment details?',
    answer:
      'No. All billing transactions, wallet top-ups, and payment card handling are processed directly by Stripe using client-side PCI-compliant elements. Cloud Weaver servers and CLI clients never see, transmit, or store your raw credit card numbers.',
  },
  {
    id: 'subscription',
    question: 'Is there a subscription or commitment?',
    answer:
      'No. Cloud Weaver operates entirely on a transparent pay-as-you-go model backed by your prepaid wallet. There are no recurring monthly subscription tiers, seat licenses, or minimum spending commitments.',
  },
  {
    id: 'low-balance',
    question: 'What if I run out of balance mid-job?',
    answer:
      'The CLI delivers real-time notifications in your terminal and via webhook when your balance approaches your remaining runtime estimate. Additionally, Cloud Weaver provides a small grace buffer to ensure a job nearing completion is not abruptly killed the millisecond your wallet hits zero.',
  },
  {
    id: 'refunds',
    question: 'Can I get a refund?',
    answer:
      'Yes. You can request a refund of any unused wallet balance at any time through our support portal. Furthermore, failed reservation attempts and nodes that fail our automated hardware benchmark are never deducted from your balance in the first place, eliminating the need for dispute resolution.',
  },
];

export const FAQ: React.FC = () => {
  const [openIds, setOpenIds] = useState<Record<string, boolean>>({
    providers: true, // open first item by default for quick clarity
  });

  const toggleFAQ = (id: string) => {
    setOpenIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <section id="faq" className="w-full py-20 sm:py-24 md:py-28 px-6 sm:px-8 bg-[#ffffff] border-t border-[#e7e7e7]">
      <div className="max-w-[760px] mx-auto">
        {/* Section Header */}
        <div className="text-center mb-14 sm:mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] text-[13px] font-medium text-[#1f1f1f] tracking-[0.075em] uppercase mb-4">
            <HelpCircle className="w-3.5 h-3.5 text-[#594ff4]" />
            <span>Frequently Asked Questions</span>
          </div>
          <h2 className="text-[34px] sm:text-[44px] font-bold text-[#1f1f1f] tracking-[-0.03em] leading-[1.15]">
            Got questions? We have answers.
          </h2>
          <p className="mt-4 text-[16px] sm:text-[17px] text-[#5d5d5d] leading-[1.6]">
            Clear, plain-English details on billing, hardware validation, provider support, and wallet policies.
          </p>
        </div>

        {/* Accordion list */}
        <div className="space-y-3.5">
          {FAQS.map((faq) => {
            const isOpen = !!openIds[faq.id];

            return (
              <div
                key={faq.id}
                className="rounded-[16px] bg-[#f6f6f6] border border-transparent transition-all overflow-hidden"
              >
                <button
                  onClick={() => toggleFAQ(faq.id)}
                  className="w-full text-left p-5 sm:p-6 flex items-center justify-between gap-4 cursor-pointer focus:outline-none"
                  aria-expanded={isOpen}
                >
                  <span className="text-[16px] sm:text-[17px] font-medium text-[#1f1f1f] leading-snug">
                    {faq.question}
                  </span>
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[#5d5d5d] transition-transform duration-200 shrink-0 ${
                      isOpen ? 'rotate-180 text-[#594ff4]' : ''
                    }`}
                  >
                    <ChevronDown className="w-5 h-5" />
                  </div>
                </button>

                {isOpen && (
                  <div className="px-5 sm:px-6 pb-5 sm:pb-6 text-[15px] sm:text-[15.5px] text-[#5d5d5d] leading-[1.65] border-t border-[#e7e7e7]/60 pt-3">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
