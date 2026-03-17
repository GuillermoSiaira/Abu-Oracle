import Link from 'next/link';

export const metadata = {
  title: 'Política de Privacidad — Abu Oracle',
};

export default function PrivacyPage() {
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
            Política de Privacidad
          </h1>
          <p className="text-xs text-slate-500">Vigente desde el 1 de abril de 2026</p>
        </header>

        {/* Intro */}
        <section className="space-y-3 text-sm leading-relaxed text-slate-400">
          <p>
            Esta Política de Privacidad describe qué datos recopila Abu Oracle, cómo los
            usa y cómo los protege. Al usar el Servicio aceptás estas prácticas.
          </p>
          <p>
            Responsable del tratamiento: Guillermo Siairat —{' '}
            <span className="text-amber-400/70">hola@abu-oracle.com</span>
          </p>
        </section>

        <Divider />

        {/* 1 */}
        <Section title="1. Datos que recopilamos">
          <Table
            rows={[
              {
                dato: 'Email',
                uso: 'Autenticación y comunicaciones sobre tu cuenta',
                almacenamiento: 'Firebase Auth (Google)',
              },
              {
                dato: 'Datos de nacimiento (fecha, hora, lugar)',
                uso: 'Cómputo astrológico local. No se envían a servidores de terceros salvo el motor de cálculo propio.',
                almacenamiento: 'Navegador (localStorage). No en base de datos.',
              },
              {
                dato: 'Datos de pago',
                uso: 'Procesamiento de la membresía',
                almacenamiento: 'Paddle (no tenemos acceso a datos de tarjeta)',
              },
              {
                dato: 'Logs técnicos',
                uso: 'Diagnóstico de errores y rendimiento',
                almacenamiento: 'Google Cloud Run (se purgan en 30 días)',
              },
            ]}
          />
        </Section>

        <Divider />

        {/* 2 */}
        <Section title="2. Datos que NO recopilamos">
          <ul className="list-none space-y-1.5 pl-4">
            <Li>No almacenamos datos de nacimiento en ninguna base de datos propia.</Li>
            <Li>No rastreamos comportamiento dentro de la aplicación con cookies de terceros.</Li>
            <Li>No recopilamos datos de ubicación en tiempo real.</Li>
            <Li>No accedemos a tus contactos, micrófono ni cámara.</Li>
          </ul>
        </Section>

        <Divider />

        {/* 3 */}
        <Section title="3. Cómo usamos tus datos">
          <p>Usamos tus datos exclusivamente para:</p>
          <ul className="list-none space-y-1.5 pl-4">
            <Li>Autenticarte en el Servicio.</Li>
            <Li>Enviarte emails transaccionales (bienvenida, cambios de cuenta).</Li>
            <Li>Calcular cartas natales y campos de relocalización en nuestros servidores.</Li>
            <Li>Monitorear el uso de cuota para gestión del plan.</Li>
          </ul>
          <p>
            No usamos tus datos para publicidad, perfilado comercial ni ningún fin distinto
            a los anteriores.
          </p>
        </Section>

        <Divider />

        {/* 4 */}
        <Section title="4. Compartición de datos">
          <p>
            <strong className="text-slate-200">No vendemos ni cedemos tus datos personales
            a terceros.</strong> Los únicos sub-procesadores con acceso son:
          </p>
          <ul className="list-none space-y-1.5 pl-4">
            <Li>
              <strong className="text-slate-300">Google Firebase / Cloud Run</strong> —
              infraestructura de autenticación, base de datos y cómputo. Sujeto a la
              política de privacidad de Google.
            </Li>
            <Li>
              <strong className="text-slate-300">Paddle</strong> — procesador de pagos.
              Trata los datos de pago como responsable independiente.
            </Li>
            <Li>
              <strong className="text-slate-300">Resend</strong> — envío de emails
              transaccionales. Solo recibe tu email y el contenido del mensaje.
            </Li>
            <Li>
              <strong className="text-slate-300">Anthropic</strong> — generación de
              interpretaciones astrológicas vía API. Recibe el contexto astrológico
              (posiciones planetarias, técnicas) pero no tu email ni datos de identidad.
            </Li>
          </ul>
        </Section>

        <Divider />

        {/* 5 */}
        <Section title="5. Almacenamiento y seguridad">
          <p>
            Tus datos de nacimiento se almacenan en el{' '}
            <code className="text-amber-400/60 text-xs">localStorage</code> de tu navegador
            y no salen de tu dispositivo excepto para el cómputo astrológico en tiempo real
            (sin persistencia en servidor).
          </p>
          <p>
            El email se almacena en Firebase Auth con encriptación en reposo. Usamos HTTPS
            para toda comunicación entre cliente y servidor.
          </p>
          <p>
            No podemos garantizar seguridad absoluta. En caso de brecha de seguridad que
            afecte datos personales, te notificaremos dentro de las 72 horas de detectarla.
          </p>
        </Section>

        <Divider />

        {/* 6 */}
        <Section title="6. Tus derechos">
          <p>Podés ejercer en cualquier momento:</p>
          <ul className="list-none space-y-1.5 pl-4">
            <Li><strong className="text-slate-300">Acceso</strong> — solicitar qué datos tenemos sobre vos.</Li>
            <Li><strong className="text-slate-300">Rectificación</strong> — corregir datos incorrectos.</Li>
            <Li><strong className="text-slate-300">Eliminación</strong> — solicitar que eliminemos tu cuenta y email asociado.</Li>
            <Li><strong className="text-slate-300">Portabilidad</strong> — recibir tus datos en formato legible por máquina.</Li>
          </ul>
          <p>
            Para ejercer cualquiera de estos derechos, escribinos a{' '}
            <span className="text-amber-400/70">hola@abu-oracle.com</span>. Respondemos en
            un máximo de 30 días.
          </p>
        </Section>

        <Divider />

        {/* 7 */}
        <Section title="7. Cookies">
          <p>
            Abu Oracle usa únicamente cookies técnicas estrictamente necesarias para la
            sesión (Firebase Auth). No usamos cookies de análisis ni publicitarias de
            terceros.
          </p>
        </Section>

        <Divider />

        {/* 8 */}
        <Section title="8. Retención de datos">
          <p>
            Tu email se conserva mientras tu cuenta esté activa. Si eliminás tu cuenta, lo
            eliminamos de Firebase Auth en un plazo de 30 días. Los logs técnicos se purgan
            automáticamente a los 30 días.
          </p>
        </Section>

        <Divider />

        {/* 9 */}
        <Section title="9. Modificaciones">
          <p>
            Podemos actualizar esta política. Si los cambios son materiales, te notificaremos
            por email. La versión vigente siempre estará en{' '}
            <span className="text-amber-400/70">abu-oracle.com/privacy</span>.
          </p>
        </Section>

        <Divider />

        {/* 10 */}
        <Section title="10. Contacto">
          <p>
            Responsable: Guillermo Siairat<br />
            <span className="text-amber-400/70">hola@abu-oracle.com</span>
          </p>
        </Section>

        {/* Footer nav */}
        <footer className="pt-6 border-t border-slate-800 flex gap-6 text-xs text-slate-500">
          <Link href="/terms-and-conditions" className="hover:text-amber-400 transition-colors">
            Términos de Servicio
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
      <div className="space-y-3 text-sm leading-relaxed">{children}</div>
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

function Table({
  rows,
}: {
  rows: { dato: string; uso: string; almacenamiento: string }[];
}) {
  return (
    <div className="border border-slate-800 rounded-md overflow-hidden text-xs">
      <div className="grid grid-cols-3 bg-slate-900/60 px-3 py-2 font-mono uppercase tracking-wider text-slate-500 text-[10px]">
        <span>Dato</span>
        <span>Uso</span>
        <span>Dónde se guarda</span>
      </div>
      {rows.map((row, i) => (
        <div
          key={i}
          className="grid grid-cols-3 px-3 py-2.5 border-t border-slate-800 text-slate-400 gap-2"
        >
          <span className="text-slate-300">{row.dato}</span>
          <span>{row.uso}</span>
          <span>{row.almacenamiento}</span>
        </div>
      ))}
    </div>
  );
}
