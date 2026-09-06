import React, { useState } from 'react';
import { Terminal, Search, CheckCircle2, Gauge, Clock, ShieldAlert, Sparkles } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(3);

  const steps = [
    {
      number: '01',
      icon: Terminal,
      title: 'You ask for a GPU.',
      shortDesc: 'One command, zero friction',
      body: 'One command, one line — no manual account setup with any GPU provider, no individual API credentials, and no complicated YAML config files. You specify the GPU architecture, minimum VRAM, or budget ceiling directly in your terminal.',
      cliSnippet: 'cloudweaver run --gpu RTX_4090 --max-price 0.50',
      badge: 'Single Command',
    },
    {
      number: '02',
      icon: Search,
      title: 'We check every marketplace at once.',
      shortDesc: 'Live real-time aggregation',
      body: 'Cloud Weaver queries live prices and node availability across every connected provider simultaneously in real time. We do not rely on cached listings or stale marketplace feeds that go outdated in seconds.',
      cliSnippet: 'Connecting to Vast.ai (420 nodes), RunPod (380 nodes)...',
      badge: 'Real-time Query',
    },
    {
      number: '03',
      icon: CheckCircle2,
      title: "We don't trust the price — we test it.",
      shortDesc: 'The core differentiator',
      body: 'We actually attempt the reservation for real. If the booking fails — whether because the listing was phantom ghost inventory, already snatched by a competing bidder, or hosted on an unresponsive machine — it is silently discarded. The next-cheapest verified option is tested automatically without interrupting you.',
      cliSnippet: 'Reservation attempt #1: Node uncontactable [DISCARDED] → Reserving next-cheapest candidate...',
      badge: 'Core Differentiator',
    },
    {
      number: '04',
      icon: Gauge,
      title: 'We inspect the hardware before you ever see it.',
      shortDesc: 'Boot-time hardware benchmark',
      body: 'Once an instance boots, Cloud Weaver runs a microscopic automated hardware benchmark before handing over the terminal. We query nvidia-smi for actual PCIe link width, measure sustained power draw against manufacturer rated spec, and execute a sub-second matrix test. If the card is power-throttled or thermally clamped, we discard it and re-roll invisibly.',
      cliSnippet: 'Diagnostic probe: RTX 4090 power target 450W / measured 448W peak. PCIe Gen4 x16 confirmed.',
      badge: 'Hardware Verification',
    },
    {
      number: '05',
      icon: Clock,
      title: 'Only then do you get billed.',
      shortDesc: 'Per-second metered billing',
      body: 'You never pay a single cent for any discarded reservation or failed hardware check behind the scenes. Billing begins solely after a healthy, benchmarked machine is verified and your SSH credentials are generated, metered strictly per second from your prepaid wallet balance.',
      cliSnippet: 'Session verified. Wallet balance $20.00. Metering active at $0.000105/sec.',
      badge: 'Zero-Waste Billing',
    },
  ];

  return (
    <section id="how-it-works" className="w-full py-20 sm:py-24 md:py-28 px-6 sm:px-8 bg-[#ffffff]">
      <div className="max-w-[1100px] mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-[760px] mx-auto mb-16 sm:mb-20">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] text-[13px] font-medium text-[#1f1f1f] tracking-[0.075em] uppercase mb-4">
            <Sparkles className="w-3.5 h-3.5 text-[#594ff4]" />
            <span>Under The Hood</span>
          </div>
          <h2 className="text-[34px] sm:text-[44px] md:text-[50px] font-bold text-[#1f1f1f] tracking-[-0.03em] leading-[1.12]">
            What actually happens when you run a job
          </h2>
          <p className="mt-4 text-[16px] sm:text-[18px] text-[#5d5d5d] leading-[1.6]">
            A complete walkthrough of the verification pipeline behind every GPU invocation — engineered so you never waste compute budget on broken hardware.
          </p>
        </div>

        {/* Steps sequence */}
        <div className="space-y-6 sm:space-y-8">
          {steps.map((step, idx) => {
            const IconComponent = step.icon;
            const isHighlighted = idx === 2 || idx === activeStep; // Step 3 is core differentiator

            return (
              <div
                key={step.number}
                onClick={() => setActiveStep(idx)}
                className={`p-6 sm:p-8 md:p-10 rounded-[32px] sm:rounded-[36px] transition-all duration-200 border cursor-pointer ${
                  isHighlighted
                    ? 'bg-[#f6f6f6] border-[#594ff4]/40 ring-1 ring-[#594ff4]/20 shadow-sm'
                    : 'bg-[#ffffff] border-[#e7e7e7] hover:border-[#b0b0b0]'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-start gap-6 lg:gap-10">
                  {/* Left: Step number & icon badge */}
                  <div className="flex items-center lg:flex-col lg:items-center gap-4 shrink-0">
                    <div className="w-14 h-14 rounded-2xl bg-white border border-[#e7e7e7] flex items-center justify-center text-[#594ff4] shadow-sm">
                      <IconComponent className="w-7 h-7 stroke-[1.75]" />
                    </div>
                    <span className="font-mono text-[18px] font-bold text-[#888888] tracking-wider">
                      {step.number}
                    </span>
                  </div>

                  {/* Middle: Content */}
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2.5 mb-2">
                      <span className="px-3 py-0.5 rounded-full text-[12px] font-medium tracking-wide bg-[#ffffff] border border-[#e7e7e7] text-[#594ff4]">
                        {step.badge}
                      </span>
                    </div>

                    <h3 className="text-[20px] sm:text-[24px] font-bold text-[#1f1f1f] tracking-[-0.015em] mb-3">
                      {step.title}
                    </h3>

                    <p className="text-[15px] sm:text-[16px] text-[#5d5d5d] leading-[1.65] max-w-[850px]">
                      {step.body}
                    </p>

                    {/* CLI snippet evidence block */}
                    <div className="mt-4 p-3.5 sm:p-4 rounded-xl bg-[#1f1f1f] text-[#f6f6f6] font-mono text-[12.5px] sm:text-[13px] overflow-x-auto border border-[#333333] flex items-center gap-2">
                      <span className="text-[#594ff4] font-bold select-none">&gt;</span>
                      <span className="text-[#e7e7e7]">{step.cliSnippet}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Highlighted Callout Box: Interruptible Pricing Handling */}
        <div className="mt-12 sm:mt-16 p-8 sm:p-10 rounded-[36px] bg-[#f6f6f6] border border-[#e7e7e7] relative overflow-hidden">
          <div className="flex flex-col sm:flex-row items-start gap-5">
            <div className="w-12 h-12 rounded-2xl bg-white border border-[#e7e7e7] flex items-center justify-center text-[#594ff4] shrink-0 shadow-sm">
              <ShieldAlert className="w-6 h-6 stroke-[1.75]" />
            </div>

            <div className="flex-1">
              <div className="inline-flex items-center gap-2 px-3 py-0.5 rounded-full bg-white border border-[#e7e7e7] text-[12px] font-semibold text-[#1f1f1f] mb-3">
                <span className="w-2 h-2 rounded-full bg-[#594ff4]"></span>
                <span>Automatic Protection</span>
              </div>

              <h4 className="text-[20px] sm:text-[22px] font-bold text-[#1f1f1f] tracking-[-0.015em] mb-2">
                Interruptible pricing: we handle spot reclaims automatically.
              </h4>

              <p className="text-[15px] sm:text-[16px] text-[#5d5d5d] leading-[1.65]">
                The cheapest GPU tiers across cloud marketplaces use spot or interruptible capacity, which can theoretically be reclaimed by the provider at any moment. When this occurs, Cloud Weaver detects the eviction event instantly and stops billing in that exact second. You never pay for compute that was pulled out from under your active job.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
