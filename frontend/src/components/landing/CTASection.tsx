export function CTASection() {
  return (
    <section className="py-24 mb-12">
      <div className="glass-card p-12 md:p-16 rounded-3xl relative overflow-hidden text-center border-primary/20">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/10 blur-[120px] -z-10" />
        <h2 className="text-4xl md:text-5xl font-bold mb-6">Ready to map your engineering universe?</h2>
        <p className="text-base text-muted-foreground max-w-xl mx-auto mb-10">
          Join 2,000+ engineering organizations scaling their knowledge infrastructure with CodeLens.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="w-full sm:w-auto bg-primary text-primary-foreground px-10 py-4 rounded-xl font-bold hover:scale-[1.02] transition-transform glow-primary">
            Start Ingesting Knowledge
          </button>
          <button className="w-full sm:w-auto px-10 py-4 rounded-xl font-bold border border-border hover:bg-white/5 transition-all">
            Talk to an Architect
          </button>
        </div>
      </div>
    </section>
  );
}
