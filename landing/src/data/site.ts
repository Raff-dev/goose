import { NPM_URL, PYPI_URL, README_URL, REPO_URL } from "../config.ts";

export const site = {
  metadata: {
    title: "Goose — from manual checks to repeatable agent testing",
    description:
      "Goose is the open-source CLI and dashboard I built when manual testing stopped scaling: repeatable cases, readable traces, direct tool debugging, and live chat replay for LLM agents.",
    keywords: [
      "LLM testing",
      "agent testing",
      "LangChain",
      "Python CLI",
      "execution traces",
      "tool call assertions",
      "open-source dashboard",
    ],
  },
  presentation: {
    chrome: {
      brand: "Goose",
      kicker: "01-06 live walkthrough",
      appendixHref: "/appendix",
      appendixLabel: "Open appendix",
      primaryCta: { label: "View on GitHub", href: REPO_URL },
    },
    opening: {
      step: "01",
      eyebrow: "Builder scar",
      title: "Goose started when manual testing stopped being a method.",
      body:
        "I was fine while the system had one or two tools. Then the tool count, prompt routing, and side effects grew past what memory could honestly verify, and a plausible answer stopped meaning the agent had actually behaved correctly.",
      narration:
        "At first I changed the prompt, asked a few questions, and trusted that the chat sounding right meant the system was still right. That stopped working long before the agent stopped sounding confident.",
      comparison: [
        {
          label: "1-2 tools",
          title: "Manual chats still feel honest",
          description:
            "You tweak the prompt, ask a few questions, and the answer sounds fine enough to move on.",
        },
        {
          label: "15-20 tools",
          title: "Plausible output stops meaning correct behavior",
          description:
            "One small prompt change can silently skip a tool, change a branch, or write the wrong file while the answer still sounds plausible.",
        },
      ],
      loopLabel: "What broke first",
      loopSteps: [
        "Change the system prompt.",
        "Ask a few manual questions.",
        "Get a plausible answer.",
        "Miss the broken tool path.",
      ],
      bridge: "So the first thing I needed was a rerunnable case, not another manual check.",
    },
    cli: {
      step: "02",
      eyebrow: "Repeatability",
      title: "The first fix was a case I could rerun.",
      body:
        "When prompt edits could quietly break half the tool stack, I stopped trusting memory. Goose cases keep the query, the expectation in plain English, and the exact tools the agent should call.",
      codeLabel: "behavior_case.py",
      code: `from goose.testing import Goose\nfrom my_agent import get_weather\n\n\ndef test_weather_query(weather_goose: Goose) -> None:\n    weather_goose.case(\n        query=\"What's the weather like in San Francisco?\",\n        expectations=[\n            \"Agent provides weather information for San Francisco\",\n            \"Response mentions sunny weather and 75°F\",\n        ],\n        expected_tool_calls=[get_weather],\n    )`,
      callouts: [
        {
          label: "Query",
          title: "Start with the real request",
          description:
            "Lock the scenario once, then rerun the same behavior after every prompt, tool, or workflow change.",
        },
        {
          label: "Expectations",
          title: "Keep the assertion human-readable",
          description:
            "Natural-language expectations survive wording drift much better than brittle regex rules.",
        },
        {
          label: "Tool calls",
          title: "Verify the path, not just the answer",
          description:
            "If the tool path matters, Goose checks that too instead of trusting a polished final response.",
        },
      ],
      bridge: "The CLI gave me repeatability. Then the logs became the next bottleneck.",
    },
    testing: {
      step: "03",
      eyebrow: "Readability",
      title: "The CLI gave me repeatability. The UI gave me orientation.",
      body:
        "Once I could rerun cases, the next bottleneck was finding the failing path fast enough. The Testing view keeps run history, expectations, tool calls, and trace detail in one place.",
      screenshot: {
        src: "/images/dashboard-view.png",
        alt: "Goose testing history view",
      },
      detail: {
        src: "/images/detail-view.png",
        alt: "Goose failing trace detail",
      },
      callouts: [
        {
          title: "History stays visible",
          description:
            "Open the failing run instead of replaying the whole story from scratch every time something drifts.",
        },
        {
          title: "Trace detail stays attached",
          description:
            "See expectations, tool calls, and outputs in the same path instead of stitching clues together from logs.",
        },
      ],
      bridge:
        "Seeing the failing path faster exposed a different absurdity: I was still running the whole agent just to debug one tool.",
    },
    tooling: {
      step: "04",
      eyebrow: "Isolation",
      title: "Then I got tired of booting the whole agent for one tool.",
      body:
        "Once the failing path was visible, a different absurdity showed up: I still had to run the entire agent to debug one tool. Tooling cuts straight to the tool, with real arguments and immediate output.",
      toolName: "get_weather",
      argsLabel: "Arguments",
      args: `{\n  \"location\": \"San Francisco\",\n  \"unit\": \"fahrenheit\"\n}`,
      outputLabel: "Result",
      output: `{\n  \"location\": \"San Francisco\",\n  \"temperature\": \"75°F\",\n  \"condition\": \"sunny\"\n}`,
      proofPoints: [
        {
          title: "No full-agent overkill",
          description:
            "Debug the tool directly instead of recreating the whole conversation just to reach it.",
        },
        {
          title: "Inputs and outputs stay explicit",
          description:
            "Arguments, results, and failures sit side by side instead of hiding behind the final answer.",
        },
      ],
      bridge: "Tooling fixed isolation, but real user bugs do not arrive as prewritten test cases.",
    },
    chat: {
      step: "05",
      eyebrow: "Real requests",
      title: "Real bugs do not arrive as prewritten test cases.",
      body:
        "When someone reports a request outside the suite, I want to replay it live first, see the tool calls and outputs, and only then decide whether it belongs in coverage.",
      events: [
        {
          kind: "user",
          label: "User request",
          text: "Compare today's weather in San Francisco with tomorrow and tell me if I should bike.",
        },
        {
          kind: "tool_call",
          label: "Tool call",
          text: "get_weather({\"location\": \"San Francisco\", \"unit\": \"fahrenheit\"})",
        },
        {
          kind: "tool_output",
          label: "Tool output",
          text: "today: 75°F and sunny, tomorrow: 68°F with light wind",
        },
        {
          kind: "assistant",
          label: "Assistant",
          text: "Bike today. Tomorrow is still fine, but it will be cooler and windier.",
        },
      ],
      nextSteps: [
        "Replay the live request.",
        "Inspect the tool arguments and output.",
        "Decide whether the edge case belongs in the suite.",
      ],
      bridge: "First I understand the live request. Then I decide what deserves to become coverage.",
    },
    close: {
      step: "06",
      eyebrow: "Closed loop",
      title: "The point was never three tabs. It was one closed loop.",
      body:
        "Once I could replay a real request, read the failing path, isolate one tool, and save the result as a case, Goose finally felt like a system instead of a pile of workarounds.",
      loop: [
        {
          label: "01",
          title: "Replay the request",
          description: "Start from the real input instead of guessing what the user probably meant.",
        },
        {
          label: "02",
          title: "Read the path",
          description: "Open the failing trace and see expectations, tool calls, and outputs together.",
        },
        {
          label: "03",
          title: "Isolate one tool",
          description: "Cut out the full-agent overhead when the bug is lower in the stack.",
        },
        {
          label: "04",
          title: "Save and rerun",
          description: "Turn the discovered behavior into coverage you can keep running on every change.",
        },
      ],
      contribution:
        "Goose only started feeling complete when I could move from a real request to saved coverage without guessing in between. If you have an edge case it does not cover yet, open an issue or send a PR.",
      primaryCta: { label: "Explore Goose on GitHub", href: REPO_URL },
      secondaryCta: { label: "Open issues", href: `${REPO_URL}/issues` },
      appendixCta: { label: "Open appendix", href: "/appendix" },
    },
  },
  appendix: {
    eyebrow: "After the talk",
    title: "Appendix: install, FAQ, and the original redacted prompt",
    intro:
      "The main route stays lean on purpose. Everything denser lives here: install commands, deeper questions, and the prompt that started the page.",
    primaryCta: { label: "Back to the presentation", href: "/" },
    secondaryCtas: [
      { label: "View on GitHub", href: REPO_URL },
      { label: "Install from PyPI", href: PYPI_URL },
    ],
  },
  nav: {
    brand: "Goose",
    links: [
      { label: "Why it breaks", href: "#problem" },
      { label: "Workflow", href: "#features" },
      { label: "Views", href: "#views" },
      { label: "Quickstart", href: "#quickstart" },
      { label: "FAQ", href: "#faq" },
    ],
    primaryCta: { label: "View on GitHub", href: REPO_URL },
  },
  hero: {
    eyebrow: "Open-source testing for LLM agents",
    title: "Test LLM agents by behavior, not regex.",
    subtitle:
      "Python library, CLI, and dashboard for validating agent behavior with natural-language expectations, tool-call checks, and execution traces you can inspect when a run drifts.",
    supportingPoints: [
      "Write a test once. Rerun it whenever prompts, tools, or workflows change.",
      "See the exact path across Testing, Tooling, and Chat instead of reconstructing failures from logs.",
      "Keep file-based results and persistent history that developers and agents can inspect, diff, and rerun.",
    ],
    badgeItems: ["Python 3.13+", "MIT", "CLI + dashboard"],
    primaryCta: { label: "Explore the repo", href: REPO_URL },
    secondaryCtas: [
      { label: "Install from PyPI", href: PYPI_URL },
      { label: "npm dashboard", href: NPM_URL },
      { label: "Read the docs", href: README_URL },
    ],
    stats: [
      { value: "3", label: "modes in one toolkit: Testing, Tooling, Chat" },
      { value: "1", label: "test definition you keep rerunning as the agent evolves" },
      { value: "0", label: "regex rules needed to survive wording drift" },
    ],
  },
  problem: {
    eyebrow: "Why teams start needing tooling",
    title: "Agent demos look easy. Real agent systems don't.",
    intro:
      "A single agent with one or two tools can feel stable in a demo. The moment you connect fifteen tools, prompt routing, side effects, and file outputs, one tiny change starts leaking into everything else.",
    items: [
      {
        title: "A small prompt edit can trigger a silent regression",
        description:
          "The answer still sounds plausible, but the agent skipped a tool, wrote the wrong file, or took a different branch than you expected.",
      },
      {
        title: "Keyword checks collapse under normal LLM variation",
        description:
          "Regex can confirm a phrase. It cannot reliably tell you whether the agent actually satisfied an expectation or only paraphrased around it.",
      },
      {
        title: "More tools means more fragility",
        description:
          "Once your system has 15–20 tools, coordination becomes the hard part. You need to verify behavior and tool usage together, not as separate guesses.",
      },
      {
        title: "Debugging from logs is too slow",
        description:
          "When tests fail, developers need traces, tool output, and test history they can inspect immediately instead of reconstructing what happened from scratch.",
      },
    ],
  },
  features: {
    eyebrow: "Core workflow",
    title: "What Goose adds to the workflow",
    featured: {
      title: "Define expectations in natural language. Still assert the exact tools.",
      description:
        "Goose combines human-readable expectations with expected tool-call checks, so you can validate both what the agent meant and what it actually did.",
    },
    items: [
      {
        title: "Full execution traces",
        description:
          "Inspect tool calls, model output, validation steps, and failures without bouncing between terminals and ad hoc logging.",
      },
      {
        title: "Pytest-style fixtures",
        description:
          "Reuse agent setup across suites and keep test code close to the way Python teams already work.",
      },
      {
        title: "Hot reload while iterating",
        description:
          "Change your agent code, rerun quickly, and keep the feedback loop short while prompts and tools are still moving.",
      },
      {
        title: "Persistent history and file-based outputs",
        description:
          "Keep artifacts that are easy to diff, inspect, rerun, and hand back to other agents in your workflow.",
      },
      {
        title: "Tool playground + interactive chat",
        description:
          "Debug a tool directly, try the agent interactively, then go back to the same tests with more confidence.",
      },
    ],
  },
  views: {
    eyebrow: "Testing + tooling + debugging",
    title: "One toolkit, three ways to work",
    intro:
      "Use the same system from the terminal, in the browser, or while debugging a single tool path. Goose keeps those modes connected instead of forcing separate workflows.",
    items: [
      {
        name: "Testing",
        label: "Run suites with intent",
        description:
          "Define cases with a query, expectations, and expected tools. Re-run them after prompt, tool, or code changes without rebuilding your whole environment.",
      },
      {
        name: "Tooling",
        label: "Debug the sharp edges",
        description:
          "Inspect available tools, validate tool behavior directly, and isolate failures before they get hidden behind agent wording.",
      },
      {
        name: "Chat",
        label: "Probe behavior live",
        description:
          "Use an interactive chat surface to explore what changed, then compare that behavior against repeatable tests and trace history.",
      },
    ],
  },
  traces: {
    eyebrow: "Failure analysis",
    title: "When something breaks, Goose shows the path to the bug",
    body:
      "Instead of asking whether the agent felt correct, you can inspect the path it took: what tools ran, what the validator accepted, what failed, and where the regression started to drift.",
    bullets: [
      "See trace context for a failing run, not just a pass/fail badge.",
      "Compare expected tool calls against the path the agent actually took.",
      "Move from a broken chat answer to the responsible prompt, tool, or fixture faster.",
    ],
    steps: [
      "Run a case from the CLI or dashboard.",
      "Open the failing trace and inspect expectations, tool calls, and outputs.",
      "Fix the prompt, tool, or fixture and rerun the same case with history intact.",
    ],
  },
  quickstart: {
    eyebrow: "Install + first case",
    title: "Get started in minutes",
    intro:
      "Install the Python package, add the dashboard CLI, and write a first case that reads like a human expectation instead of a brittle text-matching rule.",
    installLabel: "Install Goose",
    installSnippet: `pip install llm-goose\nnpm install -g @llm-goose/dashboard-cli`,
    commandsLabel: "CLI and dashboard",
    commandsSnippet: `goose init\ngoose test run tests\ngoose api\ngoose-dashboard`,
    codeLabel: "Minimal test",
    codeSnippet: `from goose.testing import Goose\nfrom my_agent import get_weather\n\n\ndef test_weather_query(weather_goose: Goose) -> None:\n    weather_goose.case(\n        query=\"What's the weather like in San Francisco?\",\n        expectations=[\n            \"Agent provides weather information for San Francisco\",\n            \"Response mentions sunny weather and 75°F\",\n        ],\n        expected_tool_calls=[get_weather],\n    )`,
    notes: [
      "Use natural-language expectations for the outcome you want.",
      "Assert expected tool usage when the path matters as much as the answer.",
      "Rerun the same case after prompt and tool changes instead of rewriting checks every sprint.",
    ],
  },
  faq: {
    eyebrow: "Questions developers ask first",
    title: "FAQ",
    items: [
      {
        q: "What exactly is Goose?",
        a: "Goose is an open-source Python library, CLI, and web dashboard for building, testing, and debugging LLM agents. It focuses on validating behavior and tool usage, not just producing a polished demo answer.",
      },
      {
        q: "Why not just use regex or keyword assertions?",
        a: "Because LLMs vary wording even when they behave correctly. Goose lets you describe expectations in natural language while also checking the tools the agent should have used.",
      },
      {
        q: "Does Goose only work for the browser dashboard?",
        a: "No. The workflow spans Python tests, a CLI, and a dashboard. You can run suites in the terminal, inspect history in the UI, and debug tools directly.",
      },
      {
        q: "Can I keep using pytest-style patterns?",
        a: "Yes. Goose uses pytest-inspired fixtures so teams can reuse setup code and keep testing close to familiar Python workflows.",
      },
      {
        q: "What kind of bugs is Goose best at catching?",
        a: "Prompt regressions, wrong tool selection, skipped tool calls, silent workflow drift, and failures where the final answer sounds plausible but the path was wrong.",
      },
      {
        q: "Is Goose production-ready?",
        a: "Goose is open source and evolving fast. It is already useful for serious agent iteration, especially when you need repeatable validation and better visibility into failures.",
      },
    ],
  },
  finalCta: {
    eyebrow: "Open-source workflow",
    title: "Build the agent. Keep the regressions visible.",
    body:
      "Goose gives you a repeatable way to test agent behavior, inspect failures, and keep tool-heavy systems from drifting silently as prompts and code evolve.",
    primaryCta: { label: "Explore Goose on GitHub", href: REPO_URL },
    secondaryCtas: [
      { label: "Install from PyPI", href: PYPI_URL },
      { label: "Open the README", href: README_URL },
    ],
  },
  promptOrigin: {
    eyebrow: "One prompt, one landing page",
    title: "This page started with one redacted prompt.",
    body:
      "Same voice, same intent — lightly cleaned up for readability, redactions preserved, and formatted to read without horizontal scrolling.",
    label: "redacted-init-prompt.txt",
    code: [
      "﻿dobra słuchaj, obczaj to repo:",
      "https://github.com/Raff-dev/goose",
      "znajdziesz je w:",
      "/home/raff/projects/personal/goose [REDACTED]",
      "repo [REDACTED]",
      "przebadaj, czym jest to repozytorium, podlinkuj tam",
      "socialki, mojego githuba itd., [REDACTED], i zobacz,",
      "jakie problemy to repozytorium rozwiązuje.",
      "",
      "ta strona ma być prezentacją, którą pokażę na wystąpieniu,",
      "więc ma opowiadać historię, dlaczego to w ogóle powstało.",
      "",
      "robisz sobie apkę agentową i wszystko jest fajnie, kiedy",
      "masz jednego toola, dwa, zmieniasz system prompt,",
      "przetestujesz to, pogadasz z agentem i widzisz, że działa.",
      "",
      "ale potem dorzucasz kolejne dwa toole, kolejne, masz już",
      "15 tooli, 20 tooli i zaczyna się prawdziwy problem.",
      "zmieniasz jedną rzecz, która potencjalnie wpływa na całego",
      "agenta, np. system prompt, i nagle robi się kłopot.",
      "",
      "goose pozwala pisać expectations w języku naturalnym.",
      "czemu? bo llm może odpowiadać różnymi sformułowaniami",
      "i nie da się tego dobrze testować deterministycznie,",
      "sprawdzając regex albo keywordy.",
      "",
      "no i wtedy wchodzi goose cały na biało:",
      "robisz expectations językiem naturalnym, wpisujesz,",
      "jakie toole powinny się wykonać. piszesz test raz",
      "i za każdym razem masz potwierdzenie, że działa —",
      "zero ręcznego testowania.",
      "",
      "goose jest toolsetem do robienia i testowania agentów.",
      "masz tam test cases, możesz bezpośrednio wywoływać",
      "toole, żeby je debugować. masz też chat, który pokazuje,",
      "co dzieje się pod spodem: z jakimi argumentami agent",
      "wywołuje jakie toole i jakie outputy przychodzą.",
      "",
      "przede wszystkim goose został zrobiony tak,",
      "żeby był agent-friendly — masz outputy w plikach,",
      "twój agent może odpalać testy, patrzeć na wyniki,",
      "masz historię i regresje. bajka.",
      "",
      "jedno stanowisko pracy mniej. chciałbym, żebyś [REDACTED]",
      "content na tę prezentację i pomysł, a później podzielił",
      "to na sekcje, dobrał odpowiednie komponenty do danych",
      "sekcji i zaimplementował całość. pamiętaj, że to pójdzie",
      "do publicznego repo i ma być opublikowane na gh pages.",
      "",
      "działaj. powodzenia żołnierzu!.",
    ].join("\n"),
  },
  footer: {
    blurb:
      "Open-source toolkit for building, testing, and debugging LLM agents with repeatable expectations, tool assertions, and visible traces.",
    groups: [
      {
        title: "Project",
        links: [
          { label: "GitHub repo", href: REPO_URL },
          { label: "README", href: README_URL },
          { label: "Issues", href: `${REPO_URL}/issues` },
        ],
      },
      {
        title: "Install",
        links: [
          { label: "PyPI package", href: PYPI_URL },
          { label: "npm dashboard CLI", href: NPM_URL },
        ],
      },
      {
        title: "Author",
        links: [
          { label: "GitHub profile", href: "https://github.com/Raff-dev" },
          { label: "LinkedIn", href: "https://www.linkedin.com/in/rlazicki/" },
          { label: "Instagram", href: "https://instagram.com/raffcodes" },
        ],
      },
    ],
  },
} as const;

export type SiteData = typeof site;
