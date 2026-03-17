import Link from 'next/link';

export const metadata = {
  title: 'Términos de Servicio — Abu Oracle',
};

export default function TermsPage() {
  return (
    <main className="min-h-full overflow-y-auto px-6 py-12">
      <div className="max-w-2xl mx-auto space-y-10 text-slate-300">

        {/* Header */}
        <header className="space-y-2 border-b border-slate-800 pb-6">
          <p className="text-[10px] font-mono tracking-[0.25em] uppercase text-slate-500">
            Abu Oracle
          </p>
          <h1
            className="text-3xl tracking-wide text-amber-400/90"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Términos de Servicio
          </h1>
          <p className="text-xs text-slate-500">Vigentes desde el 1 de abril de 2026</p>
        </header>

        {/* Intro */}
        <section className="space-y-3 text-sm leading-relaxed">
          <p>
            Al acceder o utilizar Abu Oracle (el "Servicio"), aceptás estos Términos de Servicio
            en su totalidad. Si no los aceptás, no uses el Servicio.
          </p>
          <p>
            Abu Oracle es operado por Guillermo Siairat ("nosotros", "nos"). El Servicio está
            disponible en{' '}
            <span className="text-amber-400/70">abu-oracle.com</span> y sus subdominios.
          </p>
        </section>

        <Divider />

        {/* 1 */}
        <Section title="1. Naturaleza del Servicio">
          <p>
            Abu Oracle es una herramienta de análisis astrológico computacional. Calcula
            posiciones planetarias, campos de armonía geoespacial y genera interpretaciones
            mediante modelos de lenguaje (LLM).
          </p>
          <p>
            El Servicio se ofrece con fines informativos y de entretenimiento. Las
            interpretaciones astrológicas <strong className="text-slate-200">no constituyen
            asesoramiento médico, psicológico, financiero, legal ni de ningún otro tipo
            profesional.</strong> No debés tomar decisiones importantes basándote exclusivamente
            en el contenido generado por el Servicio.
          </p>
          <p>
            Abu Oracle no garantiza la exactitud, completitud ni utilidad de ninguna
            interpretación generada. Los resultados varían según los datos ingresados y los
            modelos LLM utilizados.
          </p>
        </Section>

        <Divider />

        {/* 2 */}
        <Section title="2. Acceso y membresía">
          <p>
            El acceso al Servicio requiere una cuenta activa. Existen dos tipos de plan:
          </p>
          <ul className="list-none space-y-1.5 pl-4">
            <Li><strong className="text-slate-200">Genesis</strong> — acceso de por vida, con
            todas las funcionalidades disponibles y futuras incluidas, a cambio de un pago único.</Li>
            <Li><strong className="text-slate-200">Free</strong> — acceso limitado sin
            garantías de continuidad.</Li>
          </ul>
          <p>
            Los pagos son procesados por Paddle (paddle.com), un revendedor autorizado. Abu
            Oracle no almacena datos de tarjetas de crédito.
          </p>
          <p>
            La membresía Genesis no es reembolsable salvo que la ley aplicable lo exija.
          </p>
        </Section>

        <Divider />

        {/* 3 */}
        <Section title="3. Uso aceptable">
          <p>Al usar el Servicio te comprometés a:</p>
          <ul className="list-none space-y-1.5 pl-4">
            <Li>Proveer datos de nacimiento verídicos o claramente ficticios.</Li>
            <Li>No intentar acceder a cuentas de otros usuarios.</Li>
            <Li>No realizar ingeniería inversa ni scraping automatizado del Servicio.</Li>
            <Li>No usar el Servicio para actividades ilegales o que dañen a terceros.</Li>
          </ul>
        </Section>

        <Divider />

        {/* 4 */}
        <Section title="4. Propiedad intelectual">
          <p>
            El motor de cómputo (Abu Engine), el sistema de campo armónico (Harmony Field),
            los agentes LLM (Lilly Swarm) y toda la interfaz son propiedad de Abu Oracle.
            Queda prohibida su reproducción o distribución sin autorización expresa.
          </p>
          <p>
            Los datos astronómicos se obtienen de efemérides de dominio público (Swiss
            Ephemeris DE440s).
          </p>
        </Section>

        <Divider />

        {/* 5 */}
        <Section title="5. Limitación de responsabilidad">
          <p>
            El Servicio se provee <em>"tal como está"</em> sin garantías de ningún tipo,
            expresas o implícitas. En la máxima medida permitida por la ley, Abu Oracle no
            será responsable por daños directos, indirectos, incidentales o consecuentes
            derivados del uso o la imposibilidad de uso del Servicio.
          </p>
        </Section>

        <Divider />

        {/* 6 */}
        <Section title="6. Modificaciones">
          <p>
            Podemos modificar estos términos en cualquier momento. Si los cambios son
            materiales, te notificaremos por email con al menos 7 días de anticipación.
            El uso continuado del Servicio tras la notificación implica aceptación.
          </p>
        </Section>

        <Divider />

        {/* 7 */}
        <Section title="7. Ley aplicable">
          <p>
            Estos términos se rigen por las leyes de la República Argentina. Cualquier
            disputa se someterá a los tribunales ordinarios de la Ciudad Autónoma de Buenos
            Aires.
          </p>
        </Section>

        <Divider />

        {/* 8 */}
        <Section title="8. Contacto">
          <p>
            Para consultas sobre estos términos:{' '}
            <span className="text-amber-400/70">hola@abu-oracle.com</span>
          </p>
        </Section>

        {/* Footer nav */}
        <footer className="pt-6 border-t border-slate-800 flex gap-6 text-xs text-slate-500">
          <Link href="/privacy" className="hover:text-amber-400 transition-colors">
            Política de Privacidad
          </Link>
          <Link href="/" className="hover:text-amber-400 transition-colors">
            Volver al inicio
          </Link>
        </footer>

      </div>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm font-mono tracking-widest uppercase text-amber-400/60">{title}</h2>
      <div className="space-y-3 text-sm leading-relaxed text-slate-400">{children}</div>
    </section>
  );
}

function Divider() {
  return <div className="w-12 h-px bg-amber-500/15" />;
}

function Li({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex gap-2 text-slate-400">
      <span className="text-amber-500/40 mt-0.5 shrink-0">·</span>
      <span>{children}</span>
    </li>
  );
}
