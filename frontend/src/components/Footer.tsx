import React from 'react';
import { Github, Mail, ArrowUpRight } from 'lucide-react';

interface FooterProps {
  onScrollTo: (id: string) => void;
}

const LEGAL_BASE_URL = 'https://gpu-broker-api.onrender.com';

export const Footer: React.FC<FooterProps> = ({ onScrollTo }) => {
  const handleScrollTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer id="footer" className="w-full bg-[#1f1f1f] text-white pt-16 pb-12 px-6 sm:px-8 border-t border-[#333333]">
      <div className="max-w-[1100px] mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 lg:gap-12 pb-14 border-b border-[#333333]">
          {/* Left / Top: Brand Name + One-line restatement */}
          <div className="md:col-span-5 flex flex-col justify-between">
            <div>
              <button
                onClick={handleScrollTop}
                className="text-left font-bold text-[22px] tracking-tight text-white hover:text-[#594ff4] transition-colors flex items-center gap-2 cursor-pointer"
              >
                <span className="w-2.5 h-2.5 rounded-full bg-[#594ff4]"></span>
                <span>Cloud Weaver</span>
              </button>
              <p className="mt-4 text-[15px] text-[#b0b0b0] leading-[1.6] max-w-[340px]">
                The CLI that verifies GPU inventory and hardware performance before you&apos;re ever charged.
              </p>
            </div>

            <div className="mt-6 text-[13px] text-[#888888]">
              Automated multi-provider brokering for AI researchers &amp; engineers.
            </div>
          </div>

          {/* Right Columns: Grouped Links */}
          <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-8">
            {/* Column 1: Product Links */}
            <div>
              <h4 className="text-[13px] font-semibold text-[#888888] uppercase tracking-[0.08em] mb-4">
                Product
              </h4>
              <ul className="space-y-3">
                <li>
                  <button
                    onClick={() => onScrollTo('how-it-works')}
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer text-left"
                  >
                    How it works
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onScrollTo('pricing')}
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer text-left"
                  >
                    Pricing
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onScrollTo('faq')}
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer text-left"
                  >
                    FAQ
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onScrollTo('install')}
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer text-left"
                  >
                    Install CLI
                  </button>
                </li>
              </ul>
            </div>

            {/* Column 2: Legal Links */}
            <div>
              <h4 className="text-[13px] font-semibold text-[#888888] uppercase tracking-[0.08em] mb-4">
                Legal
              </h4>
              <ul className="space-y-3">
                <li>
                  <a
                    href={`${LEGAL_BASE_URL}/terms`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer"
                  >
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a
                    href={`${LEGAL_BASE_URL}/privacy`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href={`${LEGAL_BASE_URL}/refund`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors cursor-pointer"
                  >
                    Refund Policy
                  </a>
                </li>
              </ul>
            </div>

            {/* Column 3: Community & Contact */}
            <div>
              <h4 className="text-[13px] font-semibold text-[#888888] uppercase tracking-[0.08em] mb-4">
                Community
              </h4>
              <ul className="space-y-3">
                <li>
                  <a
                    href="https://github.com/chideraezeudu2-sudo/cloudweaver"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors inline-flex items-center gap-1.5"
                  >
                    <Github className="w-4 h-4" />
                    <span>GitHub</span>
                    <ArrowUpRight className="w-3 h-3 opacity-60" />
                  </a>
                </li>
                <li>
                  <a
                    href="mailto:support@cloudweaver.dev"
                    className="text-[15px] text-[#b0b0b0] hover:text-white transition-colors inline-flex items-center gap-1.5"
                  >
                    <Mail className="w-4 h-4" />
                    <span>support@cloudweaver.dev</span>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Final line at the very bottom */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[13px] text-[#888888]">
          <p>© 2026 Cloud Weaver. All rights reserved.</p>
          <p className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#594ff4]"></span>
            <span>Live · Multi-Provider Broker</span>
          </p>
        </div>
      </div>
    </footer>
  );
};
