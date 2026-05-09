# FIX-C02 — Auth redirect + empty chart state

## Contexto

Dos problemas en el flujo de onboarding de usuario nuevo:

**Problema 1 — Redirect post-registro a `/chart` sin datos**
`next_app/app/auth/login/page.tsx` hace `const nextPath = searchParams.get("next") || "/chart"`.
Cuando un usuario se registra (sin venir de un link con `?next=`), aterriza en `/chart`
con `abuData = null`. El resultado es un estado vacío con texto en inglés y sin CTA.

**Problema 2 — Empty state en `/chart` poco útil**
```
No chart data loaded
Initialize Abu Engine from the start page.
```
No hay botón, no hay link, no hay dirección clara. El usuario no sabe qué hacer.

## Archivos a modificar

```
next_app/app/auth/login/page.tsx    MODIFY — default redirect a / en vez de /chart
next_app/app/chart/page.tsx         MODIFY — empty state con CTA y texto i18n
```

## Spec

### 1. `app/auth/login/page.tsx` — default redirect

Cambiar la línea:
```typescript
const nextPath = searchParams.get("next") || "/chart";
```
Por:
```typescript
const nextPath = searchParams.get("next") || "/";
```

Eso es todo el cambio. Usuarios que llegan sin `?next=` (registro desde la landing,
registro directo) aterrizan en Home y desde ahí ingresan sus datos o van al demo.
Usuarios que llegaron a `/auth/login?next=/chart` (redirección de AuthGuard)
siguen yendo a `/chart` como antes.

### 2. `app/chart/page.tsx` — empty state con CTA

Localizar el bloque `if (!ready)` que renderiza el empty state:

```tsx
if (!ready) {
  return (
    <AuthGuard>
      <div className="flex items-center justify-center h-full text-slate-500">
        <div className="text-center space-y-2">
          <p className="text-lg">No chart data loaded</p>
          <p className="text-sm opacity-70">
            Initialize Abu Engine from the start page.
          </p>
        </div>
      </div>
    </AuthGuard>
  );
}
```

Reemplazarlo por un estado con CTA localizado. Importar `Link` desde `next/link`
y `useAppStore` para leer `lang` si no está ya importado. Usar las keys de i18n
o strings inline en 4 idiomas:

```tsx
if (!ready) {
  const emptyTitle: Record<string, string> = {
    es: 'Ingresá tus datos natales para comenzar',
    en: 'Enter your birth data to get started',
    pt: 'Insira seus dados natais para começar',
    fr: 'Entrez vos données natales pour commencer',
  };
  const emptyDemo: Record<string, string> = {
    es: 'O explorá una carta de demostración',
    en: 'Or explore a demo chart',
    pt: 'Ou explore um mapa de demonstração',
    fr: 'Ou explorez un thème de démonstration',
  };
  const resolvedLang = (lang as string) in emptyTitle ? (lang as string) : 'es';

  return (
    <AuthGuard>
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-5 px-4">
          <div className="text-3xl text-amber-500/40">⟡</div>
          <p className="text-slate-400 text-sm max-w-xs">
            {emptyTitle[resolvedLang]}
          </p>
          <div className="flex flex-col gap-2 items-center">
            <Link
              href="/"
              className="text-sm font-mono text-amber-400 hover:text-amber-200 border border-amber-500/40 hover:border-amber-400/70 hover:bg-amber-500/5 rounded-sm px-5 py-2.5 transition-all"
            >
              → {resolvedLang === 'es' ? 'Ingresar mis datos' :
                 resolvedLang === 'en' ? 'Enter my data' :
                 resolvedLang === 'pt' ? 'Inserir meus dados' :
                 'Entrer mes données'}
            </Link>
            <Link
              href="/demo"
              className="text-xs font-mono text-slate-500 hover:text-slate-300 border border-slate-700/40 hover:border-slate-600/60 rounded-sm px-5 py-2 transition-all"
            >
              → {emptyDemo[resolvedLang]}
            </Link>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
```

**Nota**: `lang` ya está disponible en el scope del componente via
`const { lang } = useAppStore(...)` que seguramente ya está importado en el archivo.
Verificar si existe; si no, agregar `const lang = useAppStore(s => s.lang);`.

## Criterios de aceptación

- [ ] Registro sin `?next=` → redirect a `/`
- [ ] Login sin `?next=` → redirect a `/`
- [ ] AuthGuard en `/chart` sin datos → redirect a `/auth/login?next=/chart` (inalterado)
- [ ] `/chart` sin `abuData` muestra el ícono ⟡ + texto localizado + 2 links (datos / demo)
- [ ] Los links funcionan: `/` → Home con formulario, `/demo` → selector de celebridades
- [ ] `npx tsc --noEmit` pasa sin errores
