import React, { useState, useEffect } from 'react';
import { Copy, Check, Play, RefreshCw, Terminal, CheckCircle2, ShieldCheck, Zap, Server, Cpu, Activity, ArrowRight, CornerDownRight, Wifi } from 'lucide-react';

interface HeroProps {
  onScrollTo: (id: string) => void;
}

export type GpuType = 'RTX_4090' | 'A100_80GB' | 'H100_SXM';

interface GpuPreset {
  name: string;
  label: string;
  tabLabel: string;
  vramTag: string;
  pricePerHr: string;
  pricePerSec: string;
  vram: string;
  powerSpec: string;
  measuredPower: string;
  benchmark: string;
  tflops: string;
  port: number;
  candidatesCount: number;
  discard1: {
    provider: string;
    node: string;
    price: string;
    reason: string;
    detail: string;
  };
  discard2: {
    provider: string;
    node: string;
    price: string;
    reason: string;
    detail: string;
  };
}

const GPU_PRESETS: Record<GpuType, GpuPreset> = {
  RTX_4090: {
    name: 'NVIDIA GeForce RTX 4090',
    label: 'RTX_4090',
    tabLabel: 'RTX 4090',
    vramTag: '24GB',
    pricePerHr: '$0.38/hr',
    pricePerSec: '$0.000105/s',
    vram: '24 GB GDDR6X',
    powerSpec: '450W rated',
    measuredPower: '448W',
    benchmark: '82.6 TFLOPS FP32 (passed)',
    tflops: '82.6 TFLOPS FP32',
    port: 2204,
    candidatesCount: 38,
    discard1: {
      provider: 'Vast.ai',
      node: '#891',
      price: '$0.22/hr',
      reason: 'Host uncontactable',
      detail: 'ghost listing discarded',
    },
    discard2: {
      provider: 'RunPod',
      node: '#3120',
      price: '$0.28/hr',
      reason: 'Power capped',
      detail: '280W vs 450W spec (discarded)',
    },
  },
  A100_80GB: {
    name: 'NVIDIA A100 SXM4',
    label: 'A100_80GB',
    tabLabel: 'A100 80GB',
    vramTag: '80GB',
    pricePerHr: '$1.15/hr',
    pricePerSec: '$0.000319/s',
    vram: '80 GB HBM2e',
    powerSpec: '400W rated',
    measuredPower: '398W',
    benchmark: '312 TFLOPS Tensor (passed)',
    tflops: '312 TFLOPS Tensor',
    port: 2218,
    candidatesCount: 24,
    discard1: {
      provider: 'Vast.ai',
      node: '#1084',
      price: '$0.29/hr',
      reason: 'Host uncontactable',
      detail: 'ghost listing discarded',
    },
    discard2: {
      provider: 'RunPod',
      node: '#4412',
      price: '$0.32/hr',
      reason: 'Power capped',
      detail: '190W vs 400W spec (discarded)',
    },
  },
  H100_SXM: {
    name: 'NVIDIA H100 SXM5',
    label: 'H100_SXM',
    tabLabel: 'H100 SXM',
    vramTag: '80GB HBM3',
    pricePerHr: '$2.35/hr',
    pricePerSec: '$0.000652/s',
    vram: '80 GB HBM3',
    powerSpec: '700W rated',
    measuredPower: '695W',
    benchmark: '989 TFLOPS FP8 (passed)',
    tflops: '989 TFLOPS FP8',
    port: 2280,
    candidatesCount: 16,
    discard1: {
      provider: 'RunPod',
      node: '#6801',
      price: '$1.65/hr',
      reason: 'Instance claimed',
      detail: 'concurrent bid collision (discarded)',
    },
    discard2: {
      provider: 'Vast.ai',
      node: '#5219',
      price: '$1.80/hr',
      reason: 'PCIe bus clamped',
      detail: 'Gen3 x8 vs Gen5 x16 (discarded)',
    },
  },
};

export const Hero: React.FC<HeroProps> = ({ onScrollTo }) => {
  const [selectedGpu, setSelectedGpu] = useState<GpuType>('A100_80GB');
  const [copiedCmd, setCopiedCmd] = useState(false);
  const [copiedSsh, setCopiedSsh] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simStep, setSimStep] = useState(4); // 0 = start, 1 = query, 2 = discard1, 3 = discard2, 4 = verified & ready

  const preset = GPU_PRESETS[selectedGpu];

  const handleCopyCmd = () => {
    navigator.clipboard.writeText(`cloudweaver run --gpu ${preset.label}`);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2000);
  };

  const handleCopySsh = () => {
    navigator.clipboard.writeText(`ssh root@node-verified.cloudweaver.io -p ${preset.port}`);
    setCopiedSsh(true);
    setTimeout(() => setCopiedSsh(false), 2000);
  };

  const runSimulation = () => {
    setIsSimulating(true);
    setSimStep(0);
  };

  const handleSelectGpu = (type: GpuType) => {
    setSelectedGpu(type);
    setIsSimulating(true);
    setSimStep(0);
  };

  useEffect(() => {
    if (!isSimulating) return;

    if (simStep < 4) {
      const stepDelays = [450, 600, 600, 650];
      const timer = setTimeout(() => {
        setSimStep((prev) => prev + 1);
      }, stepDelays[simStep] || 550);
      return () => clearTimeout(timer);
    } else {
      setIsSimulating(false);
    }
  }, [isSimulating, simStep]);

  return (
    <section id="hero" className="w-full pt-14 sm:pt-18 md:pt-22 pb-16 px-6 sm:px-8">
      <div className="max-w-[1100px] mx-auto text-center flex flex-col items-center">
        {/* Section Eyebrow */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#f6f6f6] border border-[#e7e7e7] text-[13px] font-medium text-[#1f1f1f] tracking-[0.05em] uppercase mb-6 shadow-xs">
          <span className="w-2 h-2 rounded-full bg-[#594ff4] animate-pulse"></span>
          <span>Open CLI &amp; Multi-Provider Broker</span>
        </div>

        {/* Headline */}
        <h1 className="text-[36px] sm:text-[52px] md:text-[64px] lg:text-[72px] font-bold text-[#1f1f1f] tracking-[-0.03em] leading-[1.06] max-w-[960px]">
          Rent the cheapest verified GPU, from your terminal.
        </h1>

        {/* Subheadline */}
        <p className="mt-6 text-[17px] sm:text-[19px] md:text-[20px] text-[#5d5d5d] leading-[1.5] max-w-[760px] font-normal">
          Cloud Weaver doesn&apos;t just compare prices across marketplaces. It reserves the instance, checks live inventory, and benchmarks actual hardware power and performance before you&apos;re ever charged.
        </p>

        {/* Action Buttons */}
        <div className="mt-8 sm:mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => onScrollTo('install')}
            className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full text-[16px] font-medium text-white bg-[#594ff4] hover:bg-[#4d42e6] active:scale-[0.98] transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md"
            id="hero-primary-cta"
          >
            <span>Get Started</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onScrollTo('how-it-works')}
            className="inline-flex items-center justify-center px-7 py-3.5 rounded-full text-[16px] font-medium text-[#1f1f1f] bg-transparent border border-[#e7e7e7] hover:border-[#594ff4] hover:text-[#594ff4] active:scale-[0.98] transition-all duration-150 cursor-pointer"
            id="hero-secondary-cta"
          >
            See how it works
          </button>
        </div>

        {/* ========================================================= */}
        {/* BEAUTIFIED INTERACTIVE TERMINAL & GPU TEST BENCH SHOWCASE */}
        {/* ========================================================= */}
        <div className="mt-14 sm:mt-16 w-full max-w-[920px] text-left">
          {/* Top Control Bar with Segmented Pills & Quick Actions */}
          <div className="p-2 sm:p-2.5 rounded-2xl bg-[#ffffff] border border-[#e7e7e7] shadow-xs flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-4">
            {/* GPU Selector Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              <span className="text-[12.5px] text-[#888888] font-medium px-2 shrink-0 hidden md:inline-block">
                Example GPU:
              </span>
              {(['RTX_4090', 'A100_80GB', 'H100_SXM'] as GpuType[]).map((type) => {
                const opt = GPU_PRESETS[type];
                const isSelected = selectedGpu === type;
                return (
                  <button
                    key={type}
                    onClick={() => handleSelectGpu(type)}
                    className={`group relative px-3.5 py-1.5 rounded-xl text-[13px] font-medium transition-all duration-150 cursor-pointer shrink-0 flex items-center gap-2 border ${
                      isSelected
                        ? 'bg-[#1f1f1f] text-white border-[#1f1f1f] shadow-sm'
                        : 'bg-[#f6f6f6] text-[#5d5d5d] border-transparent hover:text-[#1f1f1f] hover:bg-[#ebebeb]'
                    }`}
                  >
                    <span>{opt.tabLabel}</span>
                    <span
                      className={`text-[10.5px] font-mono px-1.5 py-0.2 rounded ${
                        isSelected
                          ? 'bg-[#594ff4] text-white'
                          : 'bg-[#e7e7e7] text-[#888888] group-hover:text-[#5d5d5d]'
                      }`}
                    >
                      {opt.vramTag}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Terminal Actions: Replay & Copy */}
            <div className="flex items-center justify-end gap-2 shrink-0 border-t sm:border-t-0 pt-2 sm:pt-0 border-[#f0f0f0]">
              <button
                onClick={runSimulation}
                disabled={isSimulating}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-[13px] font-medium text-[#1f1f1f] bg-[#f6f6f6] hover:bg-[#e7e7e7] active:scale-[0.97] transition-all cursor-pointer disabled:opacity-60 border border-[#e7e7e7]"
                title="Watch real-time pre-flight verification sequence"
              >
                {isSimulating ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#594ff4]" />
                ) : (
                  <Play className="w-3.5 h-3.5 text-[#594ff4] fill-[#594ff4]" />
                )}
                <span>{isSimulating ? 'Verifying...' : 'Replay test'}</span>
              </button>

              <button
                onClick={handleCopyCmd}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-[13px] font-medium text-[#1f1f1f] bg-[#f6f6f6] hover:bg-[#e7e7e7] active:scale-[0.97] transition-all cursor-pointer border border-[#e7e7e7]"
                title="Copy command to clipboard"
              >
                {copiedCmd ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[#594ff4]" />
                    <span className="text-[#594ff4]">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-[#5d5d5d]" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Terminal Window Shell */}
          <div
            className="w-full rounded-[24px] bg-[#0e1117] text-[#f6f6f6] border border-[#232733] overflow-hidden shadow-2xl transition-all relative"
            style={{
              boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(89, 79, 244, 0.1)',
            }}
          >
            {/* Top Chrome / Window Title Bar */}
            <div className="bg-[#161a23] px-4 sm:px-5 py-3 border-b border-[#232733] flex items-center justify-between select-none">
              {/* Left: Window dots & shell identifier */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-[#ff5f56] inline-block shadow-xs"></span>
                  <span className="w-3 h-3 rounded-full bg-[#ffbd2e] inline-block shadow-xs"></span>
                  <span className="w-3 h-3 rounded-full bg-[#27c93f] inline-block shadow-xs"></span>
                </div>
                <div className="flex items-center gap-2 pl-2 border-l border-[#2c3242]">
                  <Terminal className="w-3.5 h-3.5 text-[#888888]" />
                  <span className="text-[12.5px] font-mono font-medium text-[#a0a5b5]">
                    bash — cloudweaver-cli
                  </span>
                </div>
              </div>

              {/* Right: Pre-flight status badge */}
              <div className="flex items-center gap-2">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#594ff4]/15 border border-[#594ff4]/30 text-[11.5px] font-mono font-medium text-[#b3acff]">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#594ff4]" />
                  <span className="tracking-wide uppercase text-[10.5px]">pre-flight verification</span>
                </div>
              </div>
            </div>

            {/* Terminal Screen Body */}
            <div className="p-5 sm:p-7 font-mono text-[13px] sm:text-[13.5px] leading-relaxed space-y-4 bg-[#0e1117]/95">
              {/* Preamble / pip install */}
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-[#9ca3af]">
                  <span className="text-[#594ff4] font-bold select-none">$</span>
                  <span className="text-white font-medium">pip install cloudweaver</span>
                </div>
                <div className="text-[#6b7280] text-[12px] pl-4 font-mono">
                  Successfully installed cloudweaver-v1.4.2
                </div>
              </div>

              {/* Run Command */}
              <div className="pt-2 border-t border-[#1f2430]">
                <div className="flex items-center gap-2 text-white">
                  <span className="text-[#594ff4] font-bold select-none">$</span>
                  <span className="font-semibold text-white">
                    cloudweaver run --gpu <span className="text-[#a5b4fc]">{preset.label}</span>
                  </span>
                </div>
              </div>

              {/* Querying phase */}
              <div className="pt-1 text-[#9ca3af] space-y-1 pl-4 border-l-2 border-[#594ff4]/40">
                <div className="flex items-center gap-2 text-[#e5e7eb]">
                  <Zap className="w-3.5 h-3.5 text-[#fbbf24] shrink-0 animate-pulse" />
                  <span>Querying real-time listings across Vast.ai &amp; RunPod...</span>
                </div>
                <div className="text-[#9ca3af] text-[12px]">
                  Found <span className="text-white font-medium">{preset.candidatesCount} candidate nodes</span> for {preset.name}. Sorting by verified lowest spot price.
                </div>
              </div>

              {/* Dynamic Discard & Verification Steps */}
              <div className="space-y-2.5 pt-1">
                {/* Step 1: Discard #1 */}
                {simStep >= 1 && (
                  <div className="flex items-start gap-3 p-2.5 sm:p-3 rounded-xl bg-[#1c1316]/60 border border-[#4a1d24]/60 text-[12.5px] sm:text-[13px] transition-all">
                    <span className="w-5 h-5 rounded-md bg-[#ff5f56]/20 border border-[#ff5f56]/40 text-[#ff5f56] flex items-center justify-center font-bold shrink-0 mt-0.5 select-none">
                      ✗
                    </span>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-[#fca5a5]">
                          [{preset.discard1.provider}] Node {preset.discard1.node} ({preset.discard1.price})
                        </span>
                        <span className="text-[#9ca3af]">→</span>
                        <span className="text-[#f87171] font-medium">Error: {preset.discard1.reason}</span>
                        <span className="text-[11px] px-1.5 py-0.2 rounded bg-[#ff5f56]/15 text-[#fca5a5] border border-[#ff5f56]/30 uppercase tracking-wider">
                          discarded
                        </span>
                      </div>
                      <div className="text-[11.5px] text-[#9ca3af] mt-0.5">
                        Listing marked active on marketplace API but failed ping handshakes. Zero cost incurred.
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Discard #2 */}
                {simStep >= 2 && (
                  <div className="flex items-start gap-3 p-2.5 sm:p-3 rounded-xl bg-[#1c1316]/60 border border-[#4a1d24]/60 text-[12.5px] sm:text-[13px] transition-all">
                    <span className="w-5 h-5 rounded-md bg-[#ff5f56]/20 border border-[#ff5f56]/40 text-[#ff5f56] flex items-center justify-center font-bold shrink-0 mt-0.5 select-none">
                      ✗
                    </span>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-[#fca5a5]">
                          [{preset.discard2.provider}] Node {preset.discard2.node} ({preset.discard2.price})
                        </span>
                        <span className="text-[#9ca3af]">→</span>
                        <span className="text-[#f87171] font-medium">Throttled: {preset.discard2.reason}</span>
                        <span className="text-[11px] px-1.5 py-0.2 rounded bg-[#ff5f56]/15 text-[#fca5a5] border border-[#ff5f56]/30 uppercase tracking-wider">
                          discarded
                        </span>
                      </div>
                      <div className="text-[11.5px] text-[#9ca3af] mt-0.5">
                        Pre-flight diagnostic measured hardware limit violation ({preset.discard2.detail}).
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Verified Node Check */}
                {simStep >= 3 && (
                  <div className="flex items-start gap-3 p-2.5 sm:p-3 rounded-xl bg-[#0e2218]/70 border border-[#166534]/60 text-[12.5px] sm:text-[13px] transition-all">
                    <span className="w-5 h-5 rounded-md bg-[#22c55e]/20 border border-[#22c55e]/40 text-[#4ade80] flex items-center justify-center font-bold shrink-0 mt-0.5 select-none">
                      ✓
                    </span>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-[#86efac] tracking-wide">
                          [Verified Node]
                        </span>
                        <span className="text-white font-medium">
                          Boot test passed: Full power envelope ({preset.powerSpec} (measured {preset.measuredPower})), {preset.benchmark}
                        </span>
                      </div>
                      <div className="text-[11.5px] text-[#86efac]/80 mt-0.5">
                        PCIe link validated at maximum throughput. Thermals normal. Handing over terminal...
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Step 4: Final Allocation & Direct SSH Box */}
              {simStep >= 4 && (
                <div className="mt-4 p-4 sm:p-5 rounded-2xl bg-[#141923] border border-[#2b3345] shadow-inner space-y-4">
                  {/* Allocation Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#232a3b]">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-[#594ff4]/20 border border-[#594ff4]/40 flex items-center justify-center text-[#a5b4fc]">
                        <Cpu className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-[14px] font-bold text-white tracking-tight flex items-center gap-2">
                          <span>Reserved: {preset.name}</span>
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#1e2536] text-[#9ca3af] border border-[#2f384f]">
                            {preset.vram}
                          </span>
                        </div>
                        <div className="text-[11.5px] text-[#9ca3af] mt-0.5">
                          Node allocated. Billed strictly per-second. Auto-disconnect enabled on zero balance.
                        </div>
                      </div>
                    </div>

                    {/* Price Tag Pill */}
                    <div className="shrink-0 flex items-center gap-2 self-start sm:self-center">
                      <div className="px-3 py-1 rounded-xl bg-[#594ff4]/20 border border-[#594ff4]/40 text-right">
                        <div className="text-[14px] font-bold font-mono text-[#c7d2fe]">
                          {preset.pricePerHr}
                        </div>
                        <div className="text-[10.5px] font-mono text-[#9ca3af]">
                          ({preset.pricePerSec})
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Direct SSH Command Box with Instant Copy */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#0a0d13] p-3 rounded-xl border border-[#202738]">
                    <div className="flex items-center gap-2 overflow-x-auto text-[12.5px] sm:text-[13px]">
                      <span className="text-[#888888] font-mono text-[12px] uppercase tracking-wider shrink-0 select-none">
                        Direct SSH:
                      </span>
                      <code className="text-[#4ade80] font-mono font-medium select-all whitespace-nowrap">
                        ssh root@node-verified.cloudweaver.io -p {preset.port}
                      </code>
                    </div>

                    <button
                      onClick={handleCopySsh}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-sans font-medium bg-[#1e2536] hover:bg-[#2b354d] text-white active:scale-[0.97] transition-all cursor-pointer border border-[#35405c] shrink-0"
                    >
                      {copiedSsh ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-[#4ade80]" />
                          <span className="text-[#4ade80]">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-[#9ca3af]" />
                          <span>Copy SSH</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Terminal Footer Status Bar */}
            <div className="bg-[#12161f] px-4 sm:px-5 py-2.5 border-t border-[#232733] flex flex-wrap items-center justify-between text-[11.5px] font-mono text-[#71788e] gap-2 select-none">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5 text-[#4ade80]">
                  <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-ping"></span>
                  <span>broker: online</span>
                </span>
                <span className="text-[#3a4155]">|</span>
                <span className="hidden sm:inline">inventory: 840+ nodes live</span>
                <span className="text-[#3a4155] hidden sm:inline">|</span>
                <span>latency: 14ms</span>
              </div>
              <div className="flex items-center gap-2 text-[#9ca3af]">
                <ShieldCheck className="w-3.5 h-3.5 text-[#594ff4]" />
                <span className="text-[#818cf8] font-medium">zero fee on unverified nodes</span>
              </div>
            </div>
          </div>

          {/* Small Trust Line underneath */}
          <p className="mt-4 text-center text-[14px] text-[#888888] font-normal">
            Currently supporting Vast.ai and RunPod, with more marketplaces on the way
          </p>
        </div>
      </div>
    </section>
  );
};

