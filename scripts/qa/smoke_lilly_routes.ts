type JsonObject = Record<string, unknown>;

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3001";
const TEST_TOKEN = process.env.TEST_TOKEN ?? "";

const MIN_ABU_DATA = {
  person: { name: "Test Einstein" },
  chart: {
    planets: [
      {
        name: "Sol",
        sign: "Piscis",
        house: 12,
        degree: 23.1,
        longitude: 353.1,
        dignity: "peregrine",
        retrograde: false,
      },
      {
        name: "Luna",
        sign: "Sagitario",
        house: 9,
        degree: 14.2,
        longitude: 254.2,
        dignity: "peregrine",
        retrograde: false,
      },
      {
        name: "Jupiter",
        sign: "Acuario",
        house: 11,
        degree: 11.2,
        longitude: 311.2,
        dignity: "peregrine",
        retrograde: false,
      },
    ],
    houses: [
      { house: 1, sign: "Cancer", degree: 11.5, start: 101.5 },
      { house: 10, sign: "Aries", degree: 5.2, start: 5.2 },
    ],
    ascendant: { sign: "Cancer", degree: 11.5 },
    mc: { sign: "Aries", degree: 5.2 },
  },
  derived: {
    sect: { sect: "diurnal", sect_light: "Sol" },
    profections: [
      {
        house: 12,
        sign: "Piscis",
        lord: "Jupiter",
        is_active: true,
        date_end: "2026-07-14",
      },
    ],
    firdaria: [
      {
        major_planet: "Sol",
        minor_planet: "Jupiter",
        is_active: true,
        date_end: "2028-03-14",
      },
    ],
    lots: {},
  },
};

const MIN_TIMELINE = {
  profections: MIN_ABU_DATA.derived.profections,
  firdaria: MIN_ABU_DATA.derived.firdaria,
  transits_window: [
    {
      transit_planet: "Jupiter",
      natal_planet: "Sol",
      aspect: "trine",
      exact_date: "2026-06-01",
      ingress_date: "2026-05-15",
      egress_date: "2026-06-20",
      is_active: true,
      speed_class: "slow",
    },
  ],
};

const BASE_PAYLOAD = {
  abuData: MIN_ABU_DATA,
  natalData: MIN_ABU_DATA,
  birthData: {
    birthDate: "1879-03-14",
    date: "1879-03-14",
    lat: 48.4,
    lon: 10.0,
    latitude: 48.4,
    longitude: 10.0,
    city: "Ulm",
    userName: "Test Einstein",
    utcOffset: 0,
  },
  timeline: MIN_TIMELINE,
  lang: "es",
  messages: [],
};

interface TestCase {
  route: string;
  payload: JsonObject;
  responseFields?: string[];
}

interface TestResult {
  route: string;
  status: number;
  passed: boolean;
  error?: string;
  respLen?: number;
}

function responseText(body: JsonObject, fields: string[]): string | undefined {
  for (const field of fields) {
    const value = body[field];
    if (typeof value === "string") return value;
  }
  return undefined;
}

async function testRoute(testCase: TestCase): Promise<TestResult> {
  const url = `${BASE_URL}${testCase.route}`;
  const fields = testCase.responseFields ?? ["response"];

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(TEST_TOKEN ? { Authorization: `Bearer ${TEST_TOKEN}` } : {}),
      },
      body: JSON.stringify(testCase.payload),
    });

    const body = (await res.json().catch(() => ({}))) as JsonObject;
    const fieldValue = responseText(body, fields);
    const respLen = fieldValue?.trim().length ?? 0;
    const passed = res.status === 200 && respLen > 10;

    return {
      route: testCase.route,
      status: res.status,
      passed,
      error: passed
        ? undefined
        : `status=${res.status} responseLen=${respLen} fields=${fields.join("|")}`,
      respLen,
    };
  } catch (err: unknown) {
    return {
      route: testCase.route,
      status: 0,
      passed: false,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

function buildTestCases(): TestCase[] {
  return [
    {
      route: "/api/lilly/screen-open",
      payload: {
        ...BASE_PAYLOAD,
        name: "Test Einstein",
        sect: "diurnal",
        sect_master: "Sol",
      },
    },
    {
      route: "/api/lilly/planet",
      payload: {
        ...BASE_PAYLOAD,
        planet_name: "Sol",
        lon: 353.1,
        sign: "Piscis",
        house: 12,
        dignity: "peregrine",
        dignity_score: 0,
        retrograde: false,
        planet: {
          name: "Sol",
          sign: "Piscis",
          house: 12,
          degree: 23.1,
          dignity: "peregrine",
          retrograde: false,
        },
      },
    },
    {
      route: "/api/lilly/technique",
      payload: {
        ...BASE_PAYLOAD,
        technique: "sect",
        data: { sect: "diurnal" },
      },
    },
    {
      route: "/api/lilly/transit",
      payload: {
        ...BASE_PAYLOAD,
        transit_planet: "Jupiter",
        transit_sign: "Cancer",
        transit_deg: 15.2,
        transit_date: "2026-06-01",
        aspects: [
          {
            natal_planet: "Sol",
            aspect: "trine",
            orb: 1.2,
            applying: true,
          },
        ],
        transit: {
          transit_planet: "Jupiter",
          natal_planet: "Sol",
          aspect: "trine",
          exact_date: "2026-06-01",
        },
      },
    },
    {
      route: "/api/lilly/domain",
      payload: {
        ...BASE_PAYLOAD,
        domain: "h10",
        domainLabel: "Carrera",
        house_num: 10,
        significators: ["Marte", "Sol"],
        hf_current: 0.62,
        hf_max: 0.91,
        best_city: "Viena",
      },
    },
    {
      route: "/api/lilly/city",
      payload: {
        ...BASE_PAYLOAD,
        city_name: "Buenos Aires",
        country: "AR",
        lat: -34.6,
        lon: -58.4,
        hf_score: 0.72,
        delta_natal: 0.18,
        domain: "global",
        asc_local: "Cancer",
        mc_local: "Aries",
        city: { name: "Buenos Aires", lat: -34.6, lon: -58.4, hf_score: 0.72 },
      },
    },
    {
      route: "/api/lilly/house",
      payload: {
        ...BASE_PAYLOAD,
        house_num: 1,
        cusp_sign: "Cancer",
        house_lord: "Luna",
        occupants: ["Jupiter"],
        subject_name: "Test Einstein",
      },
    },
    {
      route: "/api/lilly/sky",
      payload: {
        ...BASE_PAYLOAD,
        fastTransits: [],
        lunarData: null,
      },
    },
    {
      route: "/api/lilly/solar-return",
      payload: {
        ...BASE_PAYLOAD,
        srYear: 2026,
        sr_year: 2026,
        city: { name: "Viena", lat: 48.2, lon: 16.4 },
        domain: "h10",
        active_domain: "h10",
        active_domain_house: 10,
        house_num: 10,
        significators: ["Marte", "Sol"],
      },
    },
    {
      route: "/api/lilly/mundana",
      payload: {
        ...BASE_PAYLOAD,
        config: {
          type: "conjunction_JS",
          label: "Jupiter-Saturn conjunction",
          planets: ["Jupiter", "Saturn"],
          orb: 1.4,
          exact_date: "2026-06-01",
          p_value: 0.04,
          density_ratio: 1.8,
          significance: "medium",
        },
        historyContext: {
          sample_events: [
            {
              date: "1603-12-17",
              description: "Conjunction cycle historical sample",
              category: "political",
            },
          ],
        },
      },
    },
    {
      route: "/api/chat",
      responseFields: ["reply", "response"],
      payload: {
        ...BASE_PAYLOAD,
        message: "Cual es mi ascendente?",
        messages: [{ role: "user", content: "Cual es mi ascendente?" }],
        context: {
          calculations: MIN_ABU_DATA,
          meta: {
            date: "1879-03-14",
            lat: 48.4,
            lon: 10.0,
            city: "Ulm",
            userName: "Test Einstein",
            utcOffset: 0,
          },
        },
        meta: { date: "1879-03-14", lat: 48.4, lon: 10.0 },
      },
    },
  ];
}

async function testRateLimit(): Promise<boolean> {
  const limit = Number(process.env.FREE_TIER_LIMIT ?? 15);
  console.log(`\nRate limit test (FREE_TIER_LIMIT=${limit})\n`);

  if (!TEST_TOKEN) {
    console.log("  skipped: TEST_TOKEN is required for rate-limit testing");
    return false;
  }

  let lastStatus = 0;
  let lastText = "";
  const planetCase = buildTestCases().find((testCase) => testCase.route === "/api/lilly/planet");
  if (!planetCase) throw new Error("planet test case missing");

  for (let i = 1; i <= limit + 1; i++) {
    const res = await fetch(`${BASE_URL}/api/lilly/planet`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${TEST_TOKEN}`,
      },
      body: JSON.stringify(planetCase.payload),
    });
    lastStatus = res.status;
    const body = (await res.json().catch(() => ({}))) as JsonObject;
    lastText = responseText(body, ["response", "reply"]) ?? "";
    process.stdout.write(`  call ${i}: ${res.status}\n`);
  }

  const passed = lastStatus === 429 || /gratuitas|limite|limit/i.test(lastText);
  console.log(`\n  ${passed ? "✅" : "❌"} Call ${limit + 1} returned ${lastStatus}\n`);
  return passed;
}

async function testFirestoreLogging(): Promise<void> {
  console.log(
    "  skipped: Firestore logging test requires Firebase Admin credentials in the script environment",
  );
}

async function main(): Promise<void> {
  const runRateLimit = process.argv.includes("--rate-limit");
  const runFirestore = process.argv.includes("--firestore-logging");

  console.log("\nAbu Oracle - Smoke Test Suite");
  console.log(`   Base URL : ${BASE_URL}`);
  console.log(`   Auth     : ${TEST_TOKEN ? "present" : "MISSING - anonymous smoke only"}\n`);

  if (runRateLimit) {
    const ok = await testRateLimit();
    process.exit(ok ? 0 : 1);
  }

  if (runFirestore) {
    await testFirestoreLogging();
    process.exit(0);
  }

  const results: TestResult[] = [];
  for (const testCase of buildTestCases()) {
    results.push(await testRoute(testCase));
  }

  let passed = 0;
  for (const result of results) {
    const icon = result.passed ? "✅" : "❌";
    const extra = result.passed
      ? `(${result.respLen} chars)`
      : `ERROR: ${result.error}`;
    console.log(`  ${icon} ${result.route.padEnd(35)} ${extra}`);
    if (result.passed) passed++;
  }

  console.log(`\n  ${passed}/${results.length} routes passing\n`);
  process.exit(passed === results.length ? 0 : 1);
}

main().catch((err: unknown) => {
  console.error(err);
  process.exit(1);
});
