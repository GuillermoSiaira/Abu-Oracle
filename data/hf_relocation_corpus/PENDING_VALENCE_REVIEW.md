# Revisión de valencias pendiente — corpus de relocalización HF

> **Tarea de G.** 32 eventos quedaron marcados `valence: "0"` (neutro) por el
> agente delegado siguiendo la regla "ante duda, 0 para revisión". Muchos son
> en realidad + o − (ej. "primer sencillo" = positivo de carrera). Reclasificar
> fortalece el corpus: los neutros no aportan al test de correlación HF↔valencia.
> El sesgo actual es +111/−20 — recuperar negativos y positivos reales ayuda.

Editá la columna **nueva valencia** (`+` / `−` / dejar `0` si de verdad es neutro)
y después actualizá el JSON del sujeto en `data/hf_relocation_corpus/{sujeto}.json`
(o pedímelo y lo aplico yo en una pasada).

## bowie (3)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1962-01-01 | h10 | `0` | David Bowie formó su primera banda, los Konrads, a la edad de 15 años. |
| 1966-01-01 | h1 | `0` | Bowie lanzó su primer sencillo bajo el nombre de David Bowie, titulado 'Can't Help Thinkin… |
| 2006-01-01 | h10 | `0` | Bowie realizó su última actuación en vivo en un evento benéfico. |

## einstein (6)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1888-01-01 | h9 | `0` | Inicio de estudios en Luitpold-Gymnasium. |
| 1895-01-01 | h9 | `0` | Inicio de estudios en old Kantonsschule (Albert Einstein House). |
| 1895-01-01 | h4 | `0` | Einstein se mudó a Suiza, abandonando su ciudadanía alemana al año siguiente. |
| 1896-01-01 | h9 | `0` | Inicio de estudios en ETH Zurich. |
| 1914-01-01 | h4 | `0` | Einstein se mudó a Berlín para unirse a la Academia Prusiana de Ciencias. |
| 1939-01-01 | h11 | `0` | Einstein firmó una carta al presidente Franklin D. Roosevelt alertando sobre el potencial … |

## freud (4)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1859-01-01 | h4 | `0` | La familia Freud dejó Freiberg y se trasladó a Leipzig. |
| 1860-01-01 | h4 | `0` | La familia Freud se mudó a Viena, donde Freud creció y se educó. |
| 1876-01-01 | h10 | `0` | Freud pasó cuatro semanas en la estación de investigación zoológica de Claus en Trieste. |
| 1879-01-01 | h1 | `0` | Freud fue llamado a cumplir un año de servicio militar obligatorio. |

## gandhi (6)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1888-01-01 | h9 | `0` | Gandhi se inscribió en el Samaldas College en Bhavnagar, pero abandonó poco después. |
| 1888-08-10 | h4 | `0` | Gandhi dejó Porbandar para ir a Bombay con el objetivo de estudiar derecho en Londres. |
| 1888-09-04 | h4 | `0` | Gandhi zarpó hacia Londres para continuar sus estudios de derecho. |
| 1893-01-01 | h4 | `0` | Gandhi se trasladó a Sudáfrica para representar a un comerciante indio en un juicio. |
| 1915-01-01 | h4 | `0` | Gandhi regresó a India después de vivir 21 años en Sudáfrica. |
| 1947-08-15 | h11 | `0` | India obtuvo su independencia del dominio británico, aunque fue dividida en India y Pakist… |

## jung (3)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1900-12-01 | h4 | `0` | Jung se mudó a Zürich para comenzar como interno en el hospital psiquiátrico Burghölzli ba… |
| 1913-01-06 | h12 | `0` | Ruptura formal de relaciones profesionales y personales con Freud. |
| 1944-02-11 | h8 | `0` | Infarto de miocardio seguido de embolia pulmonar y estado de coma. |

## picasso (4)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1891-01-01 | h4 | `0` | La familia de Picasso se mudó a A Coruña, donde su padre se convirtió en profesor en la Es… |
| 1895-01-01 | h4 | `0` | Después de la muerte de su hermana, la familia se mudó a Barcelona. |
| 1897-01-01 | h9 | `0` | Inicio de estudios en Royal Academy of Fine Arts of San Fernando. |
| 1901-01-01 | h1 | `0` | Comenzó el Período Azul, caracterizado por pinturas sombrías en tonos azules. |

## tesla (4)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1870-01-01 | h9 | `0` | Inicio de estudios en Karlovac Gymnasium. |
| 1875-01-01 | h9 | `0` | Inicio de estudios en Graz University of Technology. |
| 1884-06-01 | h4 | `0` | Tesla emigró a los Estados Unidos y comenzó a trabajar en Edison Machine Works en Nueva Yo… |
| 1884-06-06 | h4 | `0` | Llegada a New York. |

## vangogh (2)

| fecha | dom | nueva val | evento |
|---|---|---|---|
| 1876-01-01 | h4 | `0` | Vincent van Gogh regresó a Inglaterra para trabajar como profesor suplente en una pequeña … |
| 1886-01-01 | h4 | `0` | Van Gogh se mudó a París, donde conoció a miembros de la vanguardia artística. |

**Total a revisar: 32**