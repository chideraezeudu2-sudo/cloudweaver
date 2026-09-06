import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { TheProblem } from './components/TheProblem';
import { HowItWorks } from './components/HowItWorks';
import { Pricing } from './components/Pricing';
import { Install } from './components/Install';
import { FAQ } from './components/FAQ';
import { FinalCTA } from './components/FinalCTA';
import { Footer } from './components/Footer';

export default function App() {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      const navOffset = 72; // header height
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - navOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });
    }
  };

  return (
    <div className="min-h-screen bg-[#ffffff] text-[#1f1f1f] flex flex-col font-sans selection:bg-[#594ff4]/15 selection:text-[#1f1f1f]">
      {/* 1. Header (sticky) */}
      <Header onScrollTo={scrollToSection} />

      {/* Main Content Sections in sequence */}
      <main className="flex-1 w-full flex flex-col items-center">
        {/* 2. Hero Section */}
        <Hero onScrollTo={scrollToSection} />

        {/* 3. The Problem Section */}
        <TheProblem />

        {/* 4. How It Works Section */}
        <HowItWorks />

        {/* 5. Pricing Section */}
        <Pricing onScrollTo={scrollToSection} />

        {/* 6. Install / Get Started Section */}
        <Install />

        {/* 7. FAQ Section */}
        <FAQ />

        {/* 8. Final CTA Section */}
        <FinalCTA onScrollTo={scrollToSection} />
      </main>

      {/* 9. Footer -- legal links go straight to the real, live policy pages
          (the single source of truth) rather than a separate hardcoded
          copy that could drift out of sync with what's actually deployed. */}
      <Footer onScrollTo={scrollToSection} />
    </div>
  );
}
