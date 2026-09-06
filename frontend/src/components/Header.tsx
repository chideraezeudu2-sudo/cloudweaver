import React, { useState } from 'react';
import { Github, Menu, X, ArrowUpRight } from 'lucide-react';

interface HeaderProps {
  onScrollTo: (id: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ onScrollTo }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (id: string) => {
    onScrollTo(id);
    setMobileMenuOpen(false);
  };

  const handleLogoClick = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  return (
    <header
      id="header"
      className="sticky top-0 z-50 w-full bg-[#ffffff]/95 backdrop-blur-md border-b border-[#e7e7e7] transition-all duration-200"
    >
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 h-[72px] flex items-center justify-between">
        {/* Left: Logo / Wordmark */}
        <button
          onClick={handleLogoClick}
          className="text-left font-bold text-[20px] sm:text-[22px] tracking-[-0.03em] text-[#1f1f1f] hover:text-[#594ff4] transition-colors focus:outline-none flex items-center gap-2 cursor-pointer"
          aria-label="Cloud Weaver - back to top"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-[#594ff4] inline-block"></span>
          <span>Cloud Weaver</span>
        </button>

        {/* Center: Anchor navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <button
            onClick={() => handleNavClick('how-it-works')}
            className="text-[15px] font-medium text-[#5d5d5d] hover:text-[#1f1f1f] transition-colors focus:outline-none cursor-pointer"
          >
            How it works
          </button>
          <button
            onClick={() => handleNavClick('pricing')}
            className="text-[15px] font-medium text-[#5d5d5d] hover:text-[#1f1f1f] transition-colors focus:outline-none cursor-pointer"
          >
            Pricing
          </button>
          <button
            onClick={() => handleNavClick('faq')}
            className="text-[15px] font-medium text-[#5d5d5d] hover:text-[#1f1f1f] transition-colors focus:outline-none cursor-pointer"
          >
            FAQ
          </button>
        </nav>

        {/* Right: Two Action Buttons */}
        <div className="hidden sm:flex items-center gap-3">
          <a
            href="https://github.com/chideraezeudu2-sudo/cloudweaver"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-full text-[14px] font-medium text-[#1f1f1f] border border-[#e7e7e7] hover:border-[#594ff4] hover:text-[#594ff4] transition-all duration-150 cursor-pointer"
            id="header-github-link"
          >
            <Github className="w-4 h-4" />
            <span>GitHub</span>
            <ArrowUpRight className="w-3.5 h-3.5 opacity-60" />
          </a>

          <button
            onClick={() => handleNavClick('install')}
            className="inline-flex items-center justify-center px-6 py-2.5 rounded-full text-[14px] font-medium text-white bg-[#594ff4] hover:bg-[#4d42e6] active:scale-[0.98] transition-all duration-150 shadow-none cursor-pointer"
            id="header-cta-button"
          >
            Get Started
          </button>
        </div>

        {/* Mobile menu toggle */}
        <div className="flex sm:hidden items-center gap-2">
          <button
            onClick={() => handleNavClick('install')}
            className="px-3.5 py-1.5 rounded-full text-[13px] font-medium text-white bg-[#594ff4]"
          >
            Install
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-[#1f1f1f] hover:text-[#594ff4] focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-[#e7e7e7] bg-white px-6 py-5 flex flex-col gap-4 animate-in slide-in-from-top-2 duration-150">
          <button
            onClick={() => handleNavClick('how-it-works')}
            className="text-left py-2 text-[16px] font-medium text-[#333333] hover:text-[#594ff4]"
          >
            How it works
          </button>
          <button
            onClick={() => handleNavClick('pricing')}
            className="text-left py-2 text-[16px] font-medium text-[#333333] hover:text-[#594ff4]"
          >
            Pricing
          </button>
          <button
            onClick={() => handleNavClick('faq')}
            className="text-left py-2 text-[16px] font-medium text-[#333333] hover:text-[#594ff4]"
          >
            FAQ
          </button>
          <div className="pt-3 border-t border-[#e7e7e7] flex flex-col gap-2.5">
            <a
              href="https://github.com/chideraezeudu2-sudo/cloudweaver"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 py-2.5 rounded-full border border-[#e7e7e7] text-[14px] font-medium text-[#1f1f1f]"
            >
              <Github className="w-4 h-4" />
              <span>GitHub Repository</span>
            </a>
            <button
              onClick={() => handleNavClick('install')}
              className="w-full py-2.5 rounded-full bg-[#594ff4] text-white text-[14px] font-medium text-center"
            >
              Get Started
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
