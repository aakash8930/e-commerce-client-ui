import Hero from "@/components/landing/Hero";
import LandingFooter from "@/components/landing/LandingFooter";
import LandingNav from "@/components/landing/LandingNav";
import LandingSections from "@/components/landing/LandingSections";

const LandingPage = () => {
  return (
    <div className="flex min-h-screen flex-col">
      <LandingNav />
      <main className="flex-1">
        <Hero />
        <LandingSections />
      </main>
      <LandingFooter />
    </div>
  );
};

export default LandingPage;
