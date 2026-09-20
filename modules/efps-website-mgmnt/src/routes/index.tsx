import { createFileRoute } from "@tanstack/react-router";
import { Helmet } from "react-helmet-async";
import ContactForm from "../components/ContactForm";
import { submitLead } from "../lib/submitLead";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  Home,
  TrendingUp,
  Settings,
  Users,
  Globe,
  BarChart2,
  Handshake,
  MapPin,
  MessageSquare,
  Search,
  CheckCircle,
  Shield,
  Zap,
  Layers,
  MessageCircle,
  Phone,
  Mail,
  Star,
  Menu,
  X,
  ArrowRight,
  CheckCircle2,
  Building,
  Calculator,
  HelpCircle,
  ArrowUpRight,
  type LucideIcon,
} from "lucide-react";

export const Route = createFileRoute("/")({
  component: Index,
});

const BUSINESS_CONFIG = {
  phone: "+91 91483 38801",
  email: "info@easyfindprops.com",
  googleMapsUrl: "https://maps.app.goo.gl/Z211hsPcT1g9ZJ9U8",
  address:
    "A Block, Prestige Atlanta, 1, 80 Feet Rd, 3rd Block, Koramangala 8th Block, Bengaluru 560034",
  stats: {
    clients: "500+",
    rating: "4.9★",
    years: "5+",
    deals: "1000+",
  },
};

type Service = {
  icon: LucideIcon;
  name: string;
  desc: string;
  bullets: string[];
};

const SERVICES: Service[] = [
  {
    icon: Home,
    name: "Rental Services",
    desc: "Find the right tenant faster and close with confidence.",
    bullets: [
      "Tenant sourcing & qualified leads",
      "Property listing & marketing",
      "Site visit coordination",
      "Negotiation & deal closure",
      "Rental agreement support",
    ],
  },
  {
    icon: TrendingUp,
    name: "Property Sales (Buy & Sell)",
    desc: "Buy right or sell faster with the right strategy.",
    bullets: [
      "Buyer requirement understanding",
      "Verified property sourcing",
      "Property marketing for sellers",
      "Price negotiation support",
      "End-to-end deal closure",
    ],
  },
  {
    icon: Settings,
    name: "Property Management",
    desc: "Complete property care without the daily hassle.",
    bullets: [
      "Tenant management",
      "Rent collection & tracking",
      "Maintenance coordination",
      "Property inspections",
      "Owner updates & reporting",
    ],
  },
  {
    icon: Users,
    name: "Tenant Management",
    desc: "Hassle-free tenant handling from entry to exit.",
    bullets: [
      "Tenant onboarding & verification",
      "Rent follow-ups",
      "Issue resolution handling",
      "Renewal & exit coordination",
      "Owner communication",
    ],
  },
  {
    icon: Globe,
    name: "NRI Property Assistance",
    desc: "Manage your Bangalore property from anywhere.",
    bullets: [
      "End-to-end remote management",
      "Tenant handling & rent tracking",
      "Maintenance & repairs",
      "Legal & documentation support",
      "Regular owner updates",
    ],
  },
  {
    icon: BarChart2,
    name: "Investment Advisory",
    desc: "Make smarter property decisions with the right guidance.",
    bullets: [
      "High ROI opportunities",
      "Rental yield analysis",
      "Bangalore location insights",
      "Risk evaluation",
      "Long-term planning support",
    ],
  },
  {
    icon: Handshake,
    name: "End-to-End Support",
    desc: "Support at every step — from search to closure.",
    bullets: [
      "Documentation assistance",
      "Agreement support",
      "Negotiation guidance",
      "Coordination between parties",
      "Smooth transaction execution",
    ],
  },
  {
    icon: MapPin,
    name: "Relocation Assistance",
    desc: "Move to Bangalore with ease and clarity.",
    bullets: [
      "Area guidance & shortlisting",
      "Property shortlisting",
      "Virtual & physical tours",
      "Relocation coordination",
      "Local move-in assistance",
    ],
  },
];

const REVIEWS = [
  {
    text: "They are very helpful and professional. They showed us good flats and even negotiated the rent on our behalf. They ensured all the rules and regulations of the owners were easily communicated to us before the token payment. Highly recommend them.",
    name: "Rishabh Kejariwal",
  },
  {
    text: "Excellent brokerage service. Parvez, in particular, was extremely professional and guided us impeccably to make our premises rental process smooth and hassle-free. Everything was managed in a very short time.",
    name: "Randhir Singh",
  },
  {
    text: "Parvez helped us find a flat in just 2-3 days. He was able to pick exactly what we were looking for and showed us houses that met our criteria. Appreciate the quick service!",
    name: "Kirit",
  },
  {
    text: "I just moved to Bangalore from the USA. Finding an apartment here is no easy task! After meeting several realtors and seeing MANY apartments, fate led me to Ahmed. He showed me three places and the third one was perfect.",
    name: "Greenstar Goddess",
  },
];

const WHY_US = [
  {
    icon: MapPin,
    title: "Local Expertise in Bangalore",
    body: "Deep knowledge of Bangalore's micro-markets, localities, and pricing.",
  },
  {
    icon: Shield,
    title: "Verified Clients & Genuine Requirements",
    body: "We work only with serious buyers, tenants, and owners.",
  },
  {
    icon: Zap,
    title: "Fast Response & Quick Turnaround",
    body: "No waiting around — we respond fast and close faster.",
  },
  {
    icon: Layers,
    title: "End-to-End Handling",
    body: "One team for the entire journey — no hand-offs, no confusion.",
  },
  {
    icon: Settings,
    title: "Property Management Support",
    body: "We stay involved after the deal — managing your property long-term.",
  },
  {
    icon: MessageCircle,
    title: "Transparent Communication",
    body: "You're always in the loop — no surprises, no hidden steps.",
  },
];

type ClusterTone = "navy" | "blue" | "warm" | "white";

type Cluster = {
  name: string;
  icon: LucideIcon;
  tone: ClusterTone;
  tagline: string;
  localities: string[];
  note: string;
  source?: {
    label: string;
    href: string;
  };
};

const CLUSTERS: Cluster[] = [
  {
    name: "ORR Tech Belt",
    icon: Building,
    tone: "navy",
    tagline:
      "Our main East Bangalore corridor, connecting established office districts and residential communities along the Outer Ring Road.",
    localities: [
      "Marathahalli",
      "Kadubeesanahalli",
      "Bellandur",
      "Devarabeesanahalli",
      "Doddanekkundi",
    ],
    note: "A continuous service corridor linking major office campuses and residential pockets along Bengaluru’s Outer Ring Road.",
  },
  {
    name: "Whitefield & ITPL Corridor",
    icon: Globe,
    tone: "blue",
    tagline: "An established East Bangalore business and residential corridor around Whitefield.",
    localities: ["Whitefield", "ITPL", "Kadugodi", "Brookefield", "Pattandur Agrahara"],
    note: "Served by the operational Purple Line, including Whitefield (Kadugodi) and Pattandur Agrahara stations.",
    source: {
      label: "BMRCL network information",
      href: "https://english.bmrc.co.in/",
    },
  },
  {
    name: "Hoodi & Mahadevapura",
    icon: Layers,
    tone: "warm",
    tagline: "A connected service pocket between Whitefield and the Outer Ring Road corridor.",
    localities: ["Hoodi", "Mahadevapura", "K.R. Puram", "Garudacharpalya", "Doddanekkundi"],
    note: "These connected neighbourhoods sit within BBMP’s Mahadevapura administrative zone in East Bengaluru.",
    source: {
      label: "BBMP ward information",
      href: "https://bbmp.gov.in/",
    },
  },
  {
    name: "Sarjapur Road Corridor",
    icon: Home,
    tone: "white",
    tagline: "A broad residential corridor linking Sarjapur Road with nearby East Bangalore areas.",
    localities: ["Sarjapur Road", "Kasavanahalli", "Harlur", "Carmelaram", "Balagere"],
    note: "A broad south-east corridor connecting established residential pockets between the Outer Ring Road and Sarjapur.",
  },
  {
    name: "Indiranagar & Old Airport Road",
    icon: MapPin,
    tone: "blue",
    tagline:
      "Two established East Bangalore service areas with residential and commercial streets.",
    localities: ["Indiranagar", "Domlur", "C.V. Raman Nagar", "HAL", "Old Airport Road"],
    note: "Indiranagar is served by the operational Purple Line, while Domlur and HAL connect toward Old Airport Road.",
    source: {
      label: "BMRCL network information",
      href: "https://english.bmrc.co.in/",
    },
  },
  {
    name: "Koramangala & HSR Layout",
    icon: Handshake,
    tone: "warm",
    tagline:
      "Established south-east Bengaluru neighbourhoods connecting residential streets, workplaces, and everyday amenities.",
    localities: ["Koramangala", "HSR Layout", "Agara", "Bommanahalli", "BTM Layout"],
    note: "HSR expands to Hosur–Sarjapur Road Layout; this cluster covers nearby service areas on both sides of the corridor.",
  },
];

const NAV_LINKS = [
  { label: "Services", href: "#services" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Areas", href: "#areas" },
  { label: "Why Choose Us", href: "#why-choose-us" },
  { label: "Reviews", href: "#reviews" },
  { label: "Contact", href: "#contact" },
];

export const NAVY = "#1A3A5C";
export const GOLD = "#C9A84C";
const SURFACE = "#F8F9FB";
const TEXT = "#1A1A2E";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";

function scrollToId(id: string) {
  const el = document.querySelector(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function Logo({ light = false }: { light?: boolean }) {
  return (
    <a
      href="#hero"
      onClick={(e) => {
        e.preventDefault();
        scrollToId("#hero");
      }}
      className="flex items-center"
      aria-label="EasyFind Property Solutions home"
    >
      <span
        className="flex items-center justify-center overflow-hidden"
        style={{
          background: light ? "#ffffff" : "transparent",
          borderRadius: light ? 10 : 0,
          padding: light ? "6px 10px" : 0,
        }}
      >
        <img
          src="/easyfind-logo.jpg"
          alt="EasyFind Property Solutions"
          style={{ height: light ? 44 : 48, width: "auto", display: "block" }}
          loading="eager"
        />
      </span>
    </a>
  );
}

function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          setScrolled(window.scrollY > 8);
          ticking = false;
        });
        ticking = true;
      }
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <Helmet>
        <title>EasyFind Property Solutions | Bangalore's Trusted Property Partner</title>
        <meta
          name="description"
          content="Bangalore's most trusted property partner for rental services, sales, management, and NRI assistance. Find, own, and manage properties with ease."
        />
        <meta
          name="keywords"
          content="Bangalore real estate, property management Bangalore, rental services Bangalore, NRI property assistance, buy sell property Bangalore"
        />
        <meta
          property="og:title"
          content="EasyFind Property Solutions | Bangalore's Trusted Property Partner"
        />
        <meta
          property="og:description"
          content="Find. Own. Manage. All under one roof. Expert property services across Bangalore."
        />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://easyfindproperties.in" />
      </Helmet>
      <header
        className="fixed inset-x-0 top-0 z-40 bg-white transition-shadow"
        style={{
          borderBottom: scrolled ? `1px solid ${BORDER}` : "1px solid transparent",
          boxShadow: scrolled ? "0 2px 16px rgba(0,0,0,0.05)" : "none",
        }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
          <Logo />
          <nav className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={(e) => {
                  e.preventDefault();
                  scrollToId(l.href);
                }}
                className="text-sm font-medium transition-colors"
                style={{ color: NAVY }}
              >
                {l.label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2 md:hidden">
            <a
              href={`tel:${BUSINESS_CONFIG.phone.replace(/\s+/g, "")}`}
              aria-label="Call EasyFind"
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold"
              style={{ background: GOLD, color: NAVY }}
            >
              <Phone size={14} />
              Call
            </a>
            <button
              aria-label="Open menu"
              onClick={() => setOpen(true)}
              className="inline-flex items-center justify-center rounded-md p-1.5"
              style={{ color: NAVY }}
            >
              <Menu size={26} />
            </button>
          </div>
          <a
            href={`tel:${BUSINESS_CONFIG.phone.replace(/\s+/g, "")}`}
            className="hidden items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold md:inline-flex"
            style={{ background: GOLD, color: NAVY }}
          >
            <Phone size={16} />
            Call Us
          </a>
        </div>

        {open && (
          <div className="fixed inset-0 z-50 flex flex-col bg-white md:hidden">
            <div
              className="flex items-center justify-between px-5 py-4"
              style={{ borderBottom: `1px solid ${BORDER}` }}
            >
              <Logo />
              <button
                aria-label="Close menu"
                onClick={() => setOpen(false)}
                style={{ color: NAVY }}
              >
                <X size={26} />
              </button>
            </div>
            <div className="flex flex-1 flex-col items-center justify-center gap-8 px-5">
              {NAV_LINKS.map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={(e) => {
                    e.preventDefault();
                    setOpen(false);
                    setTimeout(() => scrollToId(l.href), 50);
                  }}
                  className="w-full text-center text-2xl font-semibold py-2"
                  style={{ color: NAVY, borderBottom: `2px solid transparent` }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderBottomColor = GOLD)}
                  onMouseLeave={(e) => (e.currentTarget.style.borderBottomColor = "transparent")}
                >
                  {l.label}
                </a>
              ))}
              <a
                href={`tel:${BUSINESS_CONFIG.phone.replace(/\s+/g, "")}`}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg px-6 py-4 text-lg font-bold shadow-lg"
                style={{ background: GOLD, color: NAVY }}
                onClick={() => setOpen(false)}
              >
                <Phone size={20} />
                Call Us
              </a>
            </div>
          </div>
        )}
      </header>
    </>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div
      className="mb-4 text-center text-xs font-semibold uppercase"
      style={{ color: GOLD, letterSpacing: "0.2em" }}
    >
      {children}
    </div>
  );
}

function SectionTitle({ children, light = false }: { children: ReactNode; light?: boolean }) {
  return (
    <h2
      className="text-center font-bold tracking-tight"
      style={{
        color: light ? "#fff" : NAVY,
        fontFamily: "'Playfair Display', Inter, serif",
        fontSize: "clamp(28px, 4vw, 40px)",
        lineHeight: 1.15,
      }}
    >
      {children}
    </h2>
  );
}

function Hero({ onPrivacyClick }: { onPrivacyClick: () => void }) {
  return (
    <section
      id="hero"
      className="relative flex min-h-[90vh] items-center pt-24 md:pt-32"
      style={{ background: NAVY }}
    >
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-12 px-5 lg:grid-cols-2 md:px-8">
        <div className="flex flex-col justify-center text-center lg:text-left items-center lg:items-start">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-white/90">
            <span className="flex h-2 w-2 rounded-full bg-green-400 animate-pulse" />
            Bangalore's Trusted Property Partner
          </div>
          <h1
            className="font-bold text-white"
            style={{
              fontFamily: "'Playfair Display', Inter, serif",
              fontSize: "clamp(34px, 5.5vw, 60px)",
              lineHeight: 1.05,
              letterSpacing: "-0.02em",
            }}
          >
            Find. Own. Manage.
            <br />
            <span style={{ color: GOLD }}>All Under One Roof.</span>
          </h1>
          <p
            className="mt-5 max-w-xl text-base md:text-lg"
            style={{ color: "rgba(255,255,255,0.75)", lineHeight: 1.65 }}
          >
            From finding the right home to managing and selling your property, EasyFind Property
            Solutions handles it all across Bangalore. We help owners and clients move faster, avoid
            delays, and make the right decisions.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4 lg:justify-start">
            <button
              onClick={() => scrollToId("#lead-form")}
              className="rounded-lg px-8 py-4 text-base font-bold shadow-lg transition-transform hover:-translate-y-1"
              style={{ background: GOLD, color: NAVY }}
            >
              Talk to Us
            </button>
            <button
              onClick={() => scrollToId("#how-it-works")}
              className="rounded-lg border-2 px-8 py-4 text-base font-bold text-white transition-all hover:bg-white/10"
              style={{ borderColor: "rgba(255,255,255,0.3)" }}
            >
              How It Works
            </button>
          </div>
        </div>
        <div className="relative z-10 flex items-center justify-center">
          <ContactForm onPrivacyClick={onPrivacyClick} />
        </div>
      </div>
    </section>
  );
}

function TrackRecord() {
  const stats = [
    { n: BUSINESS_CONFIG.stats.clients, l: "Happy Clients" },
    { n: BUSINESS_CONFIG.stats.rating, l: "Google Rating" },
    { n: BUSINESS_CONFIG.stats.years, l: "Years in Bangalore" },
    { n: BUSINESS_CONFIG.stats.deals, l: "Deals Closed" },
  ];
  return (
    <section className="py-12 md:py-16" style={{ background: SURFACE }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <SectionLabel>Our Track Record</SectionLabel>
        <div className="mt-8 grid grid-cols-2 gap-6 md:grid-cols-4 md:gap-10">
          {stats.map((s) => (
            <div key={s.l} className="text-center">
              <div className="mx-auto mb-3 h-px w-10" style={{ background: GOLD }} />
              <div
                className="font-extrabold"
                style={{
                  color: NAVY,
                  fontSize: "clamp(32px, 4vw, 48px)",
                  lineHeight: 1,
                  letterSpacing: "-0.02em",
                }}
              >
                {s.n}
              </div>
              <div className="mt-2 text-sm md:text-base" style={{ color: MUTED }}>
                {s.l}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ServiceModal({ service, onClose }: { service: Service; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <>
      <div
        className="fixed inset-0 z-50 backdrop-blur-sm"
        style={{ background: "rgba(26, 58, 92, 0.6)" }}
        onClick={onClose}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="relative w-full max-w-lg overflow-y-auto max-h-[90vh] rounded-2xl bg-white p-6 shadow-2xl md:p-8 pointer-events-auto">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 p-2 text-navy/40 hover:text-navy"
          >
            <X size={24} />
          </button>
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-surface text-navy">
            <service.icon size={28} />
          </div>
          <h3 className="mt-6 text-2xl font-bold text-navy">{service.name}</h3>
          <p className="mt-3 text-muted leading-relaxed">{service.desc}</p>
          <div className="mt-8">
            <h4 className="text-sm font-bold uppercase tracking-wider text-navy/40">
              Key Deliverables
            </h4>
            <ul className="mt-4 space-y-3">
              {service.bullets.map((b) => (
                <li key={b} className="flex items-start gap-3 text-sm font-medium text-navy/80">
                  <CheckCircle size={18} className="mt-0.5 shrink-0 text-gold" />
                  {b}
                </li>
              ))}
            </ul>
          </div>
          <button
            onClick={() => {
              onClose();
              scrollToId("#lead-form");
            }}
            className="mt-10 w-full rounded-xl bg-gold py-4 font-bold text-navy transition-transform hover:scale-[1.02]"
          >
            Enquire About This Service
          </button>
        </div>
      </div>
    </>
  );
}

function Services() {
  const [active, setActive] = useState<Service | null>(null);
  return (
    <section id="services" className="py-16 md:py-24" style={{ background: "#fff" }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <SectionLabel>What We Do</SectionLabel>
        <SectionTitle>End-to-End Property Services</SectionTitle>
        <p className="mx-auto mt-4 max-w-2xl text-center text-base" style={{ color: MUTED }}>
          Everything you need — from finding a home to managing your investment.
        </p>
        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {SERVICES.map((s) => {
            const Icon = s.icon;
            return (
              <button
                key={s.name}
                onClick={() => setActive(s)}
                className="group text-left rounded-xl bg-white p-6 transition-all hover:-translate-y-1"
                style={{
                  border: `1px solid ${BORDER}`,
                  boxShadow: "0 2px 16px rgba(0,0,0,0.04)",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.boxShadow = "0 12px 32px rgba(26,58,92,0.12)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.boxShadow = "0 2px 16px rgba(0,0,0,0.04)")
                }
                aria-label={`View details for ${s.name}`}
              >
                <span
                  className="flex h-11 w-11 items-center justify-center rounded-lg"
                  style={{ background: SURFACE, color: NAVY }}
                >
                  <Icon size={22} />
                </span>
                <h3 className="mt-4 text-base font-bold" style={{ color: NAVY }}>
                  {s.name}
                </h3>
                <p className="mt-2 text-sm" style={{ color: MUTED, lineHeight: 1.55 }}>
                  {s.desc}
                </p>
                <span
                  className="mt-4 inline-flex items-center gap-1 text-sm font-semibold"
                  style={{ color: GOLD }}
                >
                  View Details <ArrowRight size={14} />
                </span>
              </button>
            );
          })}
        </div>
      </div>
      {active && <ServiceModal service={active} onClose={() => setActive(null)} />}
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      icon: MessageSquare,
      n: "01",
      t: "Share Your Requirement",
      b: "Tell us what you need — property type, area, budget, and timeline.",
    },
    {
      icon: Search,
      n: "02",
      t: "We Understand Your Need",
      b: "Our team listens, asks the right questions, and maps a clear plan for you.",
    },
    {
      icon: CheckCircle,
      n: "03",
      t: "We Handle Everything Till Closure",
      b: "From shortlisting and visits to negotiation, paperwork, and handover.",
    },
  ];
  return (
    <section id="how-it-works" className="py-16 md:py-24" style={{ background: SURFACE }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <SectionLabel>The Process</SectionLabel>
        <SectionTitle>Simple. Clear. Handled.</SectionTitle>
        <div className="relative mt-12 grid grid-cols-1 gap-12 lg:grid-cols-3">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            return (
              <div key={s.n} className="relative z-10 flex flex-col items-center text-center">
                <div
                  className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl shadow-lg"
                  style={{ background: "#fff", color: GOLD }}
                >
                  <Icon size={32} />
                </div>
                <div className="mb-2 text-sm font-bold" style={{ color: GOLD }}>
                  {s.n}
                </div>
                <h3 className="mb-3 text-xl font-bold" style={{ color: NAVY }}>
                  {s.t}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  {s.b}
                </p>
                {idx < 2 && (
                  <div className="absolute left-full top-10 hidden w-full border-t-2 border-dashed border-gray-200 lg:block" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function AreasSection() {
  const cardStyles = {
    navy: {
      background: "rgba(26, 58, 92, 0.94)",
      borderColor: "rgba(255, 255, 255, 0.42)",
      color: "#ffffff",
      muted: "rgba(255, 255, 255, 0.78)",
      iconBackground: "rgba(255, 255, 255, 0.14)",
      tagBackground: "rgba(255, 255, 255, 0.12)",
      tagColor: "#ffffff",
    },
    blue: {
      background: "rgba(238, 244, 247, 0.86)",
      borderColor: "rgba(255, 255, 255, 0.92)",
      color: NAVY,
      muted: MUTED,
      iconBackground: "rgba(255, 255, 255, 0.82)",
      tagBackground: "rgba(255, 255, 255, 0.7)",
      tagColor: NAVY,
    },
    warm: {
      background: "rgba(247, 243, 232, 0.82)",
      borderColor: "rgba(255, 255, 255, 0.94)",
      color: NAVY,
      muted: MUTED,
      iconBackground: "rgba(255, 255, 255, 0.82)",
      tagBackground: "rgba(255, 255, 255, 0.72)",
      tagColor: NAVY,
    },
    white: {
      background: "rgba(255, 255, 255, 0.84)",
      borderColor: "rgba(255, 255, 255, 0.96)",
      color: NAVY,
      muted: MUTED,
      iconBackground: "rgba(238, 244, 247, 0.92)",
      tagBackground: "rgba(238, 244, 247, 0.78)",
      tagColor: NAVY,
    },
  } as const;

  return (
    <section id="areas" className="overflow-hidden py-16 md:py-24" style={{ background: SURFACE }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <SectionLabel>Areas We Cover</SectionLabel>
        <div style={{ fontFamily: '"Libre Baskerville", Georgia, serif' }}>
          <SectionTitle>East Bangalore, Mapped by Character</SectionTitle>
        </div>
        <p className="mx-auto mt-4 max-w-2xl text-center text-base" style={{ color: MUTED }}>
          We group localities by how people actually live and work — so you can choose the right
          fit, faster.
        </p>
        <div
          className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-12"
          style={{ fontFamily: '"IBM Plex Sans", Arial, sans-serif' }}
        >
          {CLUSTERS.map((c, idx) => {
            const Icon = c.icon;
            const featured = idx === 0;
            const style = cardStyles[c.tone];
            return (
              <article
                key={c.name}
                className={`group relative flex min-h-72 flex-col overflow-hidden rounded-2xl border p-6 shadow-sm backdrop-blur-md transition duration-300 motion-reduce:transition-none md:p-7 lg:min-h-80 ${
                  featured ? "lg:col-span-6" : idx < 3 ? "lg:col-span-3" : "lg:col-span-4"
                }`}
                style={{
                  background: style.background,
                  borderColor: style.borderColor,
                  boxShadow: "0 12px 36px rgba(26, 58, 92, 0.07)",
                }}
              >
                {featured && (
                  <span
                    className="mb-5 w-fit rounded-full border px-3 py-1 text-xs font-semibold"
                    style={{ borderColor: "rgba(255,255,255,0.3)", color: GOLD }}
                  >
                    Main service corridor
                  </span>
                )}
                <div className="mb-5 flex items-start gap-3">
                  <span
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/70"
                    style={{ background: style.iconBackground, color: featured ? GOLD : NAVY }}
                  >
                    <Icon aria-hidden="true" size={21} strokeWidth={1.8} />
                  </span>
                  <h3
                    className={`font-bold leading-snug ${featured ? "text-2xl md:text-3xl" : "text-xl"}`}
                    style={{
                      color: style.color,
                      fontFamily: '"Libre Baskerville", Georgia, serif',
                    }}
                  >
                    {c.name}
                  </h3>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: style.muted }}>
                  {c.tagline}
                </p>
                <div className="mt-5 flex flex-wrap gap-2">
                  {c.localities.map((loc) => (
                    <span
                      key={loc}
                      className="inline-flex items-center border-l-2 px-2 py-0.5 text-xs font-semibold"
                      style={{
                        background: style.tagBackground,
                        borderColor: GOLD,
                        color: style.tagColor,
                      }}
                    >
                      {loc}
                    </span>
                  ))}
                </div>
                <div className="mt-auto flex flex-col gap-2 pt-6">
                  <p className="flex items-center gap-1.5 text-xs" style={{ color: style.muted }}>
                    <HelpCircle aria-hidden="true" size={13} />
                    {c.note}
                  </p>
                  {c.source && (
                    <a
                      href={c.source.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex w-fit items-center gap-1 text-xs font-semibold underline underline-offset-2"
                      style={{ color: featured ? GOLD : NAVY }}
                    >
                      {c.source.label}
                      <ArrowUpRight aria-hidden="true" size={12} />
                    </a>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function WhyUs() {
  return (
    <section id="why-choose-us" className="py-16 md:py-24" style={{ background: "#fff" }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <SectionLabel>Why EasyFind</SectionLabel>
        <SectionTitle>Built on Trust. Driven by Results.</SectionTitle>
        <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {WHY_US.map((w) => {
            const Icon = w.icon;
            return (
              <div key={w.title} className="flex gap-5">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
                  style={{ background: SURFACE, color: GOLD }}
                >
                  <Icon size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-bold" style={{ color: NAVY }}>
                    {w.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed" style={{ color: MUTED }}>
                    {w.body}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Reviews() {
  return (
    <section id="reviews" className="py-16 md:py-24" style={{ background: SURFACE }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <SectionLabel>What Our Clients Say</SectionLabel>
        <SectionTitle>4.9★ Rating with 110+ Reviews</SectionTitle>
        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-2">
          {REVIEWS.map((r) => (
            <div
              key={r.name}
              className="rounded-2xl bg-white p-8 shadow-sm"
              style={{ border: `1px solid ${BORDER}` }}
            >
              <div className="mb-4 flex gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={16} fill={GOLD} color={GOLD} />
                ))}
              </div>
              <p className="text-base italic leading-relaxed" style={{ color: TEXT }}>
                “{r.text}”
              </p>
              <div className="mt-6 flex items-center justify-between">
                <div className="font-bold" style={{ color: NAVY }}>
                  {r.name}
                </div>
                <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Google Review
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-12 text-center">
          <a
            href={BUSINESS_CONFIG.googleMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border-2 px-6 py-3 font-bold transition-colors"
            style={{ borderColor: GOLD, color: NAVY }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = GOLD;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            View All Reviews on Google
          </a>
        </div>
      </div>
    </section>
  );
}

function LeadForm({ onPrivacyClick }: { onPrivacyClick: () => void }) {
  // Independent state — never reads from or writes to the hero form.
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [type, setType] = useState("Looking to Rent");
  const [location, setLocation] = useState("");
  const [budget, setBudget] = useState("");
  const [details, setDetails] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [succeeded, setSucceeded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    const trimmedName = name.trim();
    const digits = phone.replace(/\D/g, "");
    if (!trimmedName) {
      setError("Please enter your name.");
      return;
    }
    if (digits.length < 10) {
      setError("Please enter a valid mobile number.");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await submitLead({
        name: trimmedName,
        phone: digits.length === 10 ? `+91 ${digits}` : phone,
        requirement: type,
        location,
        budget,
        details,
        source: "Website Bottom Enquiry Form",
      });
      setSucceeded(true);
      setName("");
      setPhone("");
      setType("Looking to Rent");
      setLocation("");
      setBudget("");
      setDetails("");
    } catch (err) {
      console.error("Bottom form submission failed:", err);
      setError("Something went wrong. Please try again or call us.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputStyle = {
    width: "100%",
    padding: "12px 16px",
    borderRadius: "8px",
    border: `1px solid ${BORDER}`,
    background: "#fff",
    fontSize: "14px",
    outline: "none",
  };

  return (
    <section id="contact" className="py-16 md:py-24" style={{ background: "#fff" }}>
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <div className="grid grid-cols-1 gap-16 lg:grid-cols-2">
          <div id="lead-form">
            <SectionLabel>Contact Us</SectionLabel>
            <h2
              className="mb-6 font-bold"
              style={{ color: NAVY, fontSize: "clamp(28px, 4vw, 40px)", lineHeight: 1.15 }}
            >
              Tell Us What You're Looking For
            </h2>
            <p className="mb-8 text-base" style={{ color: MUTED }}>
              Fill in the form and our team will reach out shortly.
            </p>
            {succeeded ? (
              <div
                className="rounded-2xl border p-8 text-center"
                role="status"
                aria-live="polite"
                style={{ borderColor: BORDER, background: SURFACE }}
              >
                <div
                  className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full"
                  style={{ background: "#ECFDF5", color: "#059669" }}
                >
                  <CheckCircle2 size={30} />
                </div>
                <h3 className="text-lg font-bold" style={{ color: NAVY }}>
                  Thank you! We'll call you shortly.
                </h3>
                <p className="mt-2 text-sm text-gray-500">Our team will get back to you shortly.</p>
                <button
                  type="button"
                  onClick={() => setSucceeded(false)}
                  className="mt-6 rounded-lg px-5 py-2 text-sm font-semibold"
                  style={{ background: GOLD, color: NAVY }}
                >
                  Submit another requirement
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} noValidate className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <input
                    type="text"
                    placeholder="Name"
                    required
                    style={inputStyle}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onBlur={(e) => setName(e.target.value.trim())}
                    disabled={isSubmitting}
                    autoComplete="name"
                  />
                  <input
                    type="tel"
                    placeholder="Phone Number"
                    required
                    style={inputStyle}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/[^\d+ ]/g, ""))}
                    disabled={isSubmitting}
                    autoComplete="tel"
                    inputMode="tel"
                  />
                </div>
                <select
                  style={inputStyle}
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  disabled={isSubmitting}
                >
                  <option>Looking to Rent</option>
                  <option>Looking to Buy</option>
                  <option>Looking to Sell</option>
                  <option>Property Management</option>
                  <option>Tenant Support</option>
                  <option>Investment Advisory</option>
                  <option>Relocation Help</option>
                </select>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <input
                    type="text"
                    placeholder="Preferred Location"
                    style={inputStyle}
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    disabled={isSubmitting}
                  />
                  <input
                    type="text"
                    placeholder="Budget"
                    style={inputStyle}
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    disabled={isSubmitting}
                  />
                </div>
                <textarea
                  placeholder="Additional Details"
                  rows={4}
                  style={inputStyle}
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                  disabled={isSubmitting}
                />
                {error && (
                  <p className="text-sm font-medium text-red-600" role="alert">
                    {error}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-lg py-4 text-base font-bold shadow-lg transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:translate-y-0"
                  style={{ background: GOLD, color: NAVY }}
                >
                  {isSubmitting ? "Sending..." : "Submit Requirement"}
                </button>
                <p className="text-center text-xs font-medium text-gray-400">
                  We will get back to you shortly. By submitting, you agree to our{" "}
                  <button
                    type="button"
                    onClick={onPrivacyClick}
                    className="font-semibold text-navy underline decoration-gold underline-offset-2"
                  >
                    Privacy Policy
                  </button>
                  .
                </p>
              </form>
            )}
          </div>
          <div>
            <SectionLabel>Get In Touch</SectionLabel>
            <h2
              className="mb-10 font-bold"
              style={{ color: NAVY, fontSize: "clamp(28px, 4vw, 40px)", lineHeight: 1.15 }}
            >
              We're Just a Message Away
            </h2>
            <div className="space-y-10">
              <div>
                <div className="text-sm text-gray-500">Available 10 AM - 7 PM</div>
                <a
                  href={`tel:${BUSINESS_CONFIG.phone.replace(/\s+/g, "")}`}
                  className="mt-3 inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-bold shadow-sm transition-transform hover:-translate-y-0.5"
                  style={{ background: GOLD, color: NAVY }}
                >
                  <Phone size={16} />
                  Call Us Now
                </a>
              </div>
              <div className="flex gap-6">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
                  style={{ background: SURFACE, color: NAVY }}
                >
                  <Mail size={24} />
                </div>
                <div>
                  <div className="text-sm font-bold uppercase tracking-wider text-gray-400">
                    Email Us
                  </div>
                  <div className="mt-1 text-sm text-gray-500">We'll reply within 24h</div>
                  <a
                    href={`mailto:${BUSINESS_CONFIG.email}`}
                    className="mt-2 block text-xl font-bold"
                    style={{ color: NAVY }}
                  >
                    {BUSINESS_CONFIG.email}
                  </a>
                </div>
              </div>
              <div className="flex gap-6">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
                  style={{ background: SURFACE, color: NAVY }}
                >
                  <MapPin size={24} />
                </div>
                <div>
                  <div className="text-sm font-bold uppercase tracking-wider text-gray-400">
                    Visit Us
                  </div>
                  <div className="mt-1 text-sm leading-relaxed text-gray-500">
                    Prestige Atlanta, 1, 80 Feet Rd,
                    <br />
                    Koramangala 8th Block,
                    <br />
                    Bengaluru, Karnataka 560034
                  </div>
                  <a
                    href={BUSINESS_CONFIG.googleMapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 block font-bold"
                    style={{ color: GOLD }}
                  >
                    View Our Google Business Profile
                  </a>
                </div>
              </div>
            </div>
            <div
              className="mt-16 overflow-hidden rounded-2xl shadow-xl"
              style={{ border: `1px solid ${BORDER}` }}
            >
              <iframe
                title="Office Location"
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3888.4847368668495!2d77.62215847587636!3d12.94079861555562!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bae15229e6c1a61%3A0x26a05f018e301661!2sEasyFind%20Property%20Solutions!5e0!3m2!1sen!2sin!4v1710321234567!5m2!1sen!2sin"
                width="100%"
                height="300"
                style={{ border: 0 }}
                allowFullScreen
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer({ onPrivacyClick }: { onPrivacyClick: () => void }) {
  return (
    <footer
      className="pt-20 pb-10 text-white"
      style={{ background: NAVY, borderTop: `4px solid ${GOLD}` }}
    >
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        {/* Main Grid */}
        <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 md:grid-cols-4 lg:gap-16">
          {/* Column 1: Brand & Hours */}
          <div className="flex flex-col space-y-6">
            <div>
              <Logo light={true} />
            </div>
            <p className="text-sm leading-relaxed text-white/70">
              Bengaluru's premier independent property consulting agency. We simplify property
              search, management, and transactions with verified listings and professional trust.
            </p>
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: GOLD }}>
                Office Hours
              </h4>
              <ul className="space-y-2 text-sm text-white/60">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: GOLD }} />
                  <span>Mon - Sat: 9:00 AM - 7:30 PM</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
                  <span>Sunday: 10:00 AM - 5:00 PM</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Column 2: Our Services */}
          <div className="flex flex-col space-y-5">
            <h3 className="text-lg font-bold tracking-tight" style={{ color: GOLD }}>
              Our Services
            </h3>
            <ul className="flex flex-col space-y-3 text-sm text-white/70">
              <li>
                <a
                  href="#services"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToId("#services");
                  }}
                  className="transition-colors hover:text-white"
                >
                  Premium Rental Services
                </a>
              </li>
              <li>
                <a
                  href="#services"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToId("#services");
                  }}
                  className="transition-colors hover:text-white"
                >
                  Property Buy & Sell
                </a>
              </li>
              <li>
                <a
                  href="#services"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToId("#services");
                  }}
                  className="transition-colors hover:text-white"
                >
                  Property Management
                </a>
              </li>
              <li>
                <a
                  href="#services"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToId("#services");
                  }}
                  className="transition-colors hover:text-white"
                >
                  Tenant Management
                </a>
              </li>
              <li>
                <a
                  href="#services"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToId("#services");
                  }}
                  className="transition-colors hover:text-white"
                >
                  Legal Handover Support
                </a>
              </li>
            </ul>
          </div>

          {/* Column 3: Prime Localities */}
          <div className="flex flex-col space-y-5">
            <h3 className="text-lg font-bold tracking-tight" style={{ color: GOLD }}>
              Service Areas
            </h3>
            <ul className="flex flex-col space-y-2.5 text-sm text-white/70">
              {[
                "Koramangala",
                "HSR Layout",
                "Indiranagar",
                "Bellandur",
                "Sarjapur Road",
                "Whitefield",
                "Hoodi",
                "Mahadevapura",
                "Marathahalli",
                "Kadubeesanahalli",
                "ITPL",
                "Varthur",
                "Kasavanahalli",
                "Harlur",
              ].map((area) => (
                <li key={area} className="flex items-center gap-2">
                  <MapPin size={14} className="shrink-0" style={{ color: GOLD }} />
                  <span>{area}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 4: Reach Us */}
          <div className="flex flex-col space-y-5">
            <h3 className="text-lg font-bold tracking-tight" style={{ color: GOLD }}>
              Contact Us
            </h3>
            <div className="flex flex-col space-y-4 text-sm text-white/70">
              <div className="flex items-start gap-2.5">
                <MapPin size={18} className="mt-0.5 shrink-0" style={{ color: GOLD }} />
                <a
                  href={BUSINESS_CONFIG.googleMapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors leading-relaxed"
                >
                  A Block, Prestige Atlanta, 1, 80 Feet Rd, Koramangala, Bengaluru 560034
                </a>
              </div>
              <div className="flex items-center gap-2.5">
                <Phone size={16} className="shrink-0" style={{ color: GOLD }} />
                <a
                  href={`tel:${BUSINESS_CONFIG.phone.replace(/\s+/g, "")}`}
                  className="font-semibold hover:text-white transition-colors"
                >
                  Call Us Now
                </a>
              </div>

              <div className="flex items-center gap-2.5">
                <Mail size={16} className="shrink-0" style={{ color: GOLD }} />
                <a
                  href={`mailto:${BUSINESS_CONFIG.email}`}
                  className="hover:text-white transition-colors break-words"
                >
                  {BUSINESS_CONFIG.email}
                </a>
              </div>
            </div>

            {/* Quick Links / Menu */}
            <div className="pt-2">
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold text-white/50">
                {NAV_LINKS.map((l) => (
                  <a
                    key={l.href}
                    href={l.href}
                    onClick={(e) => {
                      e.preventDefault();
                      scrollToId(l.href);
                    }}
                    className="hover:text-white transition-colors"
                  >
                    {l.label}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Real Estate Trust Disclaimer */}
        <div
          className="mt-16 border-t pt-6 text-center text-xs text-white/40 leading-relaxed"
          style={{ borderColor: "rgba(255,255,255,0.08)" }}
        >
          <p className="max-w-4xl mx-auto">
            Disclaimer: EasyFind Property Solutions is an independent real estate advisory firm.
            While we strive to provide accurate, verified, and up-to-date information regarding
            property rentals, sales, and management in Bengaluru, all transactions and agreements
            are subject to direct verification between parties. Service operations are compliant
            with local Karnataka state real estate regulations.
          </p>
        </div>

        {/* Bottom Bar */}
        <div
          className="mt-8 flex flex-col items-center justify-between gap-4 border-t pt-8 md:flex-row"
          style={{ borderColor: "rgba(255,255,255,0.08)" }}
        >
          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs font-medium text-white/50 md:justify-start">
            <span>© EasyFind Property Solutions. All rights reserved.</span>
            <button
              type="button"
              onClick={onPrivacyClick}
              className="font-semibold text-white/70 underline decoration-gold underline-offset-4 transition-colors hover:text-white"
            >
              Privacy Policy
            </button>
          </div>
          <div className="text-xs font-bold uppercase tracking-widest text-white/30">
            Designed for trust in Bengaluru
          </div>
        </div>
      </div>
    </footer>
  );
}

function PrivacyModal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="privacy-title"
    >
      <button
        className="absolute inset-0 bg-navy/70 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close privacy policy"
      />
      <div className="relative max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl md:p-9">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-md p-2 text-navy/60 hover:bg-surface hover:text-navy"
          aria-label="Close privacy policy"
        >
          <X size={22} />
        </button>
        <p className="text-xs font-bold uppercase" style={{ color: GOLD, letterSpacing: "0.14em" }}>
          EasyFind Property Solutions
        </p>
        <h2 id="privacy-title" className="mt-3 pr-10 text-3xl font-bold" style={{ color: NAVY }}>
          Privacy Policy
        </h2>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: MUTED }}>
          Last updated: 17 September 2026
        </p>
        <div className="mt-7 space-y-6 text-sm leading-relaxed" style={{ color: MUTED }}>
          <section>
            <h3 className="mb-2 text-base font-bold" style={{ color: NAVY }}>
              Information we collect
            </h3>
            <p>
              When you send an enquiry, we collect the details you provide, such as your name, phone
              number, requirement, preferred location, budget, and message.
            </p>
          </section>
          <section>
            <h3 className="mb-2 text-base font-bold" style={{ color: NAVY }}>
              How we use it
            </h3>
            <p>
              We use this information to respond to your enquiry, understand your property
              requirement, provide requested services, and maintain necessary business records.
            </p>
          </section>
          <section>
            <h3 className="mb-2 text-base font-bold" style={{ color: NAVY }}>
              Form processing
            </h3>
            <p>
              Enquiries may be processed through Formspree or Google Forms. Those providers process
              submitted information under their own privacy and security terms.
            </p>
          </section>
          <section>
            <h3 className="mb-2 text-base font-bold" style={{ color: NAVY }}>
              Sharing and retention
            </h3>
            <p>
              We do not sell personal information. We share it only with service providers needed to
              process enquiries, when required by law, or with your direction. We retain it only as
              long as reasonably needed for these purposes and applicable obligations.
            </p>
          </section>
          <section>
            <h3 className="mb-2 text-base font-bold" style={{ color: NAVY }}>
              Security and your choices
            </h3>
            <p>
              We take reasonable steps to protect submitted information, but no internet
              transmission is completely secure. You may ask us to access, correct, or delete your
              enquiry information, subject to legal requirements.
            </p>
          </section>
          <section>
            <h3 className="mb-2 text-base font-bold" style={{ color: NAVY }}>
              Contact
            </h3>
            <p>
              For privacy questions or requests, email{" "}
              <a
                href={`mailto:${BUSINESS_CONFIG.email}`}
                className="font-semibold underline underline-offset-2"
                style={{ color: NAVY, textDecorationColor: GOLD }}
              >
                {BUSINESS_CONFIG.email}
              </a>
              .
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}

function Index() {
  const [showPrivacy, setShowPrivacy] = useState(false);

  return (
    <div className="min-h-screen bg-white" style={{ color: TEXT, fontFamily: "Inter, sans-serif" }}>
      <Nav />
      <main>
        <Hero onPrivacyClick={() => setShowPrivacy(true)} />
        <TrackRecord />
        <Services />
        <HowItWorks />
        <AreasSection />
        <WhyUs />
        <Reviews />
        <LeadForm onPrivacyClick={() => setShowPrivacy(true)} />
      </main>
      <Footer onPrivacyClick={() => setShowPrivacy(true)} />
      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}
    </div>
  );
}
