import marimo

__generated_with = "0.23.13"
app = marimo.App(
    width="medium",
    layout_file="layouts/ai_sept_2026.slides.json",
)


@app.cell
def _():
    import json
    import sys
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import polars as pl


    def read_json(name):
        loc = mo.notebook_location() / "public" / name
        if sys.platform == "emscripten":
            import pyodide.http

            return json.load(pyodide.http.open_url(str(loc)))
        return json.loads(Path(str(loc)).read_text())


    return alt, mo, pl, read_json


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 🤖 AI tools in OSS development
    ## Henry Schreiner
    PyHEP.dev • 9/7/2026
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 📚 Resources:

    * [Starting with Agentic AI](https://iscinumpy.dev/post/starting-with-agentic-ai/)
    * [Claude Code Reviews with Fable](https://iscinumpy.dev/post/claude-code-reviews/)
    * [SE-for-Sci](https://se-for-sci.github.io) (AI section)
    * [Scientific-Python: AI page](https://github.com/scientific-python/cookie/pull/821) (PR)
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🗓️ Timeline

    * 🚀 _November 2025: Claude Opus 4.5 + Claude Code redefines Agentic AI_
    * 🧪 March 2026: I try Copilot (Claude Sonnet 4.6) to make **flake8-lazy**
    * 💸 April 2026: I use up my Copilot credits for the first time
    * 🌐 May 2026: I use Open Source models via NRP.io heavily
    * 🤖 June 2026: I get and use a Claude OSS (Max 20x) subscription
    * 🏛️ June 2026: I also get access to the Princeton AI Sandbox (for GPT 5.5)
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### flake8-lazy - why is this significant?

    It was developed about two days after the first Python 3.15 alpha with lazy imports!
    """)
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(r"""_No prior model knowledge of lazy imports in Python!_"""),
        kind="success",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 📊 Usage

    `uvx agentsview usage daily --since 2026-01-01 --format json --breakdown`

    Using Fable with marimo pairing to analyse here

    Copilot online usage not included (`@copilot`, Copilot code review, etc)
    """)
    return


@app.cell
def usage_data(pl, read_json):
    family_colors = {
        "Claude": "#2a78d6",
        "GPT": "#1baf7a",
        "Kimi": "#eda100",
        "GLM": "#008300",
        "Other OSS": "#4a3aa7",
    }


    def _family(model):
        if model.startswith("claude"):
            return "Claude"
        if model.startswith("gpt") or model == "auto":
            return "GPT"
        if model == "kimi":
            return "Kimi"
        if model.startswith("glm"):
            return "GLM"
        return "Other OSS"


    # No filesystem glob in WASM; list the files explicitly
    usage_files = ["usage_intel.json", "usage_m1.json", "usage_m5.json"]
    _machines = [read_json(_n) for _n in usage_files]

    usage_totals = {
        _key: sum(_m["totals"][_key] for _m in _machines)
        for _key in _machines[0]["totals"]
    }
    total_sessions = sum(_m["sessionCounts"]["total"] for _m in _machines)
    usage_days = len({_day["date"] for _m in _machines for _day in _m["daily"]})

    _order = {f: i for i, f in enumerate(family_colors)}

    daily_df = (
        pl.DataFrame(
            [
                {
                    "date": _day["date"],
                    "family": _family(_mb["modelName"]),
                    "output_tokens": _mb["outputTokens"],
                    "input_tokens": _mb["inputTokens"],
                    "cost": _mb["cost"],
                }
                for _m in _machines
                for _day in _m["daily"]
                for _mb in _day["modelBreakdowns"]
            ]
        )
        .group_by("date", "family")
        .agg(pl.sum("output_tokens"), pl.sum("input_tokens"), pl.sum("cost"))
        .with_columns(
            pl.col("date").str.to_date(),
            pl.col("family").replace_strict(_order).alias("family_order"),
        )
        .sort("date", "family_order")
    )

    project_df = (
        pl.DataFrame(
            [
                {"project": _p["project"], "output_tokens": _p["outputTokens"]}
                for _m in _machines
                for _day in _m["daily"]
                for _p in _day.get("projectBreakdowns", [])
            ]
        )
        .group_by("project")
        .agg(pl.sum("output_tokens"))
        .sort("output_tokens", descending=True)
    )


    _shares = daily_df.with_columns(
        (pl.col("output_tokens") / pl.sum("output_tokens").over("date")).alias(
            "share"
        )
    ).select("date", "family", "family_order", "share")

    project_family_df = (
        pl.DataFrame(
            [
                {
                    "date": _day["date"],
                    "project": _p["project"],
                    "output_tokens": _p["outputTokens"],
                }
                for _m in _machines
                for _day in _m["daily"]
                for _p in _day.get("projectBreakdowns", [])
            ]
        )
        .with_columns(pl.col("date").str.to_date())
        .join(_shares, on="date")
        .with_columns(
            (pl.col("output_tokens") * pl.col("share"))
            .fill_nan(0)
            .alias("est_tokens")
        )
        .group_by("project", "family", "family_order")
        .agg(pl.sum("est_tokens").alias("output_tokens"))
        .sort("project", "family_order")
    )
    return (
        daily_df,
        family_colors,
        project_df,
        project_family_df,
        total_sessions,
        usage_days,
        usage_files,
        usage_totals,
    )


@app.cell(hide_code=True)
def usage_kpis(mo, total_sessions, usage_days, usage_files, usage_totals):
    mo.hstack(
        [
            mo.stat(
                f"{total_sessions:,}",
                label="Sessions",
                caption=f"{usage_days} days, {len(usage_files)} machine"
                + ("s" if len(usage_files) > 1 else ""),
                bordered=True,
            ),
            mo.stat(
                f"{usage_totals['outputTokens'] / 1e6:.0f}M",
                label="Output tokens",
                bordered=True,
            ),
            mo.stat(
                f"${usage_totals['totalCost']:,.0f}",
                label="API-equivalent cost",
                caption="covered by subscriptions",
                bordered=True,
            ),
            mo.stat(
                f"${usage_totals['cacheSavings']:,.0f}",
                label="Cache savings",
                bordered=True,
            ),
        ],
        widths="equal",
    )
    return


@app.cell(hide_code=True)
def tokens_by_family(alt, daily_df, family_colors, mo):
    tokens_chart = (
        alt.Chart(daily_df)
        .mark_bar(stroke="#fcfcfb", strokeWidth=1)
        .encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%b", grid=False, tickCount="month")),
            y=alt.Y(
                "output_tokens:Q",
                title="Output tokens / day",
                axis=alt.Axis(format="~s"),
            ),
            color=alt.Color(
                "family:N",
                title=None,
                scale=alt.Scale(
                    domain=list(family_colors), range=list(family_colors.values())
                ),
            ),
            order=alt.Order("family_order:O"),
            tooltip=[
                alt.Tooltip("date:T", format="%b %d", title="Date"),
                alt.Tooltip("family:N", title="Model family"),
                alt.Tooltip("output_tokens:Q", format=",", title="Output tokens"),
            ],
        )
        .properties(
            width="container", height=340, title="Daily output tokens by model family"
        )
        .configure_axis(
            gridColor="#e1e0d9",
            domainColor="#c3c2b7",
            tickColor="#c3c2b7",
            labelColor="#898781",
            titleColor="#52514e",
        )
        .configure_view(strokeWidth=0)
        .configure_legend(labelColor="#52514e", orient="top")
        .configure_title(color="#0b0b0b", fontSize=14, anchor="start")
    )
    mo.vstack(
        [
            tokens_chart,
            mo.accordion({"Data table": mo.ui.table(daily_df, page_size=10)}),
        ]
    )
    return


@app.cell(hide_code=True)
def projects_by_tokens(alt, family_colors, pl, project_df, project_family_df):
    _top = project_df.head(12)
    _order = _top["project"].to_list()
    _pf = project_family_df.filter(pl.col("project").is_in(_order))

    _bars = (
        alt.Chart(_pf)
        .mark_bar(size=18, stroke="#fcfcfb", strokeWidth=1)
        .encode(
            y=alt.Y("project:N", sort=_order, title=None),
            x=alt.X(
                "output_tokens:Q",
                title="Output tokens",
                axis=alt.Axis(format="~s"),
            ),
            color=alt.Color(
                "family:N",
                title=None,
                scale=alt.Scale(
                    domain=list(family_colors), range=list(family_colors.values())
                ),
            ),
            order=alt.Order("family_order:O"),
            tooltip=[
                alt.Tooltip("project:N", title="Project"),
                alt.Tooltip("family:N", title="Model family"),
                alt.Tooltip("output_tokens:Q", format=",.0f", title="Output tokens (est.)"),
            ],
        )
    )
    _labels = (
        alt.Chart(_top)
        .mark_text(align="left", dx=4, color="#52514e")
        .encode(
            y=alt.Y("project:N", sort=_order),
            x="output_tokens:Q",
            text=alt.Text("output_tokens:Q", format=".3~s"),
        )
    )
    projects_chart = (
        (_bars + _labels)
        .properties(
            width="container",
            height=320,
            title=alt.TitleParams(
                "Top projects by output tokens",
                subtitle="Model mix estimated from each day's family shares",
            ),
        )
        .configure_axis(
            gridColor="#e1e0d9",
            domainColor="#c3c2b7",
            tickColor="#c3c2b7",
            labelColor="#898781",
            titleColor="#52514e",
        )
        .configure_view(strokeWidth=0)
        .configure_legend(labelColor="#52514e", orient="top")
        .configure_title(color="#0b0b0b", fontSize=14, anchor="start", subtitleColor="#898781")
    )
    projects_chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 📈 PRs with AI assistance

    > Since Jan 1 2026, how many PRs did I make each day, and how many were made with AI assistance? (AI assistance will have `:robot:` or `Assisted-by` in the description. You can also check to see if any commits have an `Assisted-by:` trailer in them. This should be written to a json file so I can make plots later, like `ai_prs_2026.json`.

    ...

    :robot: 1000 results only covers May 6–Jul 6, so it's truncated. You're very active! Let me fetch in monthly windows to get everything since Jan 1. :robot:
    """)
    return


@app.cell
def _(pl, read_json):
    data = read_json("ai_prs_2026.json")
    df = (
      pl.DataFrame([{"day": d, **v} for d, v in data.items()])
      .with_columns(pl.col("day").str.to_date(),
                    (pl.col("total") - pl.col("ai_assisted")).alias("non_ai"))
      .sort("day")
    )
    return (df,)


@app.cell
def ai_prs_by_day(alt, df, mo, pl):
    _pr_colors = {"AI-assisted": "#2a78d6", "No AI": "#c3c2b7"}

    weekly_prs = (
        df.group_by(pl.col("day").dt.truncate("1w").alias("week"))
        .agg(pl.sum("ai_assisted"), pl.sum("non_ai"), pl.sum("total"))
        .filter(pl.col("week").dt.offset_by("6d") <= df["day"].max())  # drop partial week
        .with_columns((pl.col("ai_assisted") / pl.col("total")).alias("ai_share"))
        .sort("week")
    )

    _long = weekly_prs.unpivot(
        index="week",
        on=["ai_assisted", "non_ai"],
        variable_name="kind",
        value_name="prs",
    ).with_columns(
        pl.col("kind").replace_strict(
            {"ai_assisted": "AI-assisted", "non_ai": "No AI"}
        ),
        pl.col("kind").replace_strict({"non_ai": 0, "ai_assisted": 1}).alias(
            "kind_order"
        ),
    )

    _peak = weekly_prs.sort("total", descending=True).head(1)

    _bars = (
        alt.Chart(_long)
        .mark_bar(size=18, stroke="#fcfcfb", strokeWidth=1)
        .encode(
            x=alt.X(
                "week:T",
                title=None,
                axis=alt.Axis(format="%b", grid=False, tickCount="month"),
            ),
            y=alt.Y("prs:Q", title="PRs / week"),
            color=alt.Color(
                "kind:N",
                title=None,
                scale=alt.Scale(
                    domain=list(_pr_colors), range=list(_pr_colors.values())
                ),
            ),
            order=alt.Order("kind_order:O"),
            tooltip=[
                alt.Tooltip("week:T", format="%b %d", title="Week of"),
                alt.Tooltip("kind:N", title="Kind"),
                alt.Tooltip("prs:Q", title="PRs"),
            ],
        )
    )

    _note = (
        alt.Chart(_peak)
        .mark_text(align="right", dx=-12, baseline="middle", fontSize=13, color="#52514e")
        .encode(
            x="week:T",
            y="total:Q",
            text=alt.value("Fable 5 first available"),
        )
    )

    ai_prs_chart = (
        (_bars + _note)
        .properties(
            width="container", height=320, title="PRs per week: AI-assisted vs not"
        )
        .configure_axis(
            gridColor="#e1e0d9",
            domainColor="#c3c2b7",
            tickColor="#c3c2b7",
            labelColor="#898781",
            titleColor="#52514e",
        )
        .configure_view(strokeWidth=0)
        .configure_legend(labelColor="#52514e", orient="top")
        .configure_title(color="#0b0b0b", fontSize=14, anchor="start")
    )
    mo.vstack(
        [
            ai_prs_chart,
            mo.accordion({"Data table": mo.ui.table(weekly_prs, page_size=10)}),
        ]
    )
    return (weekly_prs,)


@app.cell(hide_code=True)
def ai_share_by_week(alt, mo, weekly_prs):
    ai_share_chart = (
        alt.Chart(weekly_prs)
        .mark_line(
            color="#2a78d6",
            strokeWidth=2,
            point=alt.OverlayMarkDef(
                filled=True,
                size=64,
                color="#2a78d6",
                stroke="#fcfcfb",
                strokeWidth=2,
            ),
        )
        .encode(
            x=alt.X(
                "week:T",
                title=None,
                axis=alt.Axis(format="%b", grid=False, tickCount="month"),
            ),
            y=alt.Y(
                "ai_share:Q",
                title="AI-assisted share of PRs",
                axis=alt.Axis(format=".0%"),
                scale=alt.Scale(domain=[0, 1]),
            ),
            tooltip=[
                alt.Tooltip("week:T", format="%b %d", title="Week of"),
                alt.Tooltip("ai_share:Q", format=".0%", title="AI share"),
                alt.Tooltip("ai_assisted:Q", title="AI-assisted"),
                alt.Tooltip("total:Q", title="Total PRs"),
            ],
        )
        .properties(
            width="container",
            height=320,
            title="Share of PRs with AI assistance (weekly)",
        )
        .configure_axis(
            gridColor="#e1e0d9",
            domainColor="#c3c2b7",
            tickColor="#c3c2b7",
            labelColor="#898781",
            titleColor="#52514e",
        )
        .configure_view(strokeWidth=0)
        .configure_title(color="#0b0b0b", fontSize=14, anchor="start")
    )
    mo.vstack(
        [
            ai_share_chart,
            mo.accordion({"Data table": mo.ui.table(weekly_prs, page_size=10)}),
        ]
    )
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""## 🧠 Mental model"""),
        mo.hstack(
            [
                mo.md(r"""
    * **Model**: reasoning and useful general facts
    * **Context**: knowledge of your project and surroundings

    Within a model, the **context** controls the output.

    A **harness** is mostly about managing context so *you* control the output.
    """),
                mo.mermaid(r"""
    graph LR
        M["🧠 Model"] --> O["🎯 Output"]
        H["⚙️ Harness"] -->|manages| C["📁 Context"] --> O
    """),
            ],
            widths=[1, 1],
            gap=2,
            align="center",
        ),
        mo.hstack(
            [
                mo.callout(mo.md(r"""**Too little context**

    Won't match your coding style, weird decisions, fails to see the big picture."""), kind="warn"),
                mo.callout(mo.md(r"""**Too much context**

    Starts to forget, gets confused. (Model dependent!)"""), kind="danger"),
            ],
            widths="equal",
            gap=2,
        ),
    ])
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""
    ## 🛠️ What is it good for?

    Reducing the amount of time you spend on:
    """),
        mo.hstack(
            [
                mo.md(r"""
    * Review
    * Exploration
    * Prototyping
    * Contributing to an unfamiliar codebase
    * Consistency
    * Fixing bugs/tests/CI
    * Writing tests
    """),
                mo.md(r"""
    * Bug hunts / cleanup
    * Throwaway work (plots, scripts)
    * Anything you don't have time for
    * Profiling / optimization
    * Anything web-related
    * Categorizing issues
    * Anything with boilerplate
    """),
            ],
            widths=[1, 1],
            gap=2,
            align="start",
        ),
        mo.md(r"""
    And it scales, once you have something working you can launch many agents or reuse it!
    """),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## ⚙️ My setup

    * AI forced to add an "AI text below" header on all PR/issue text
    * `Assisted-by: ClaudeCode:claude-fable-5` trailers on commits (manual or AI)
    * Regression test before bugfix
    * Try to keep commits short (not really effective)
    * Use `prek -a --quiet`, `uv run`, `python3`
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    You are on macOS, but have GNU sed. The github user is `henryiii`. `python3` can be used if python without dependencies is needed. Use `uv run` if in a python package.
    uv's `--python VERSION` can get any python version, like 3.8 or 3.15 (in beta).
    Use `prek -a --quiet` instead of `pre-commit run -a` for linting.

    Keep comments short and focused on information that is not obvious. Text should value the reader's time. Don't add a comment if not needed, like for something removed.

    When fixing bugs, add the regression test first and confirm it fails without the fix if possible.

    If you make a commit, follow conventional commits and add a trailer: `Assisted-by: <harness>:<model>`, where `<harness>` is the current agent harness (like ClaudeCode), and `<model>` is the AI model (Like claude-opus-4.8).

    Prefix PR descriptions and comments on PRs with the line ":robot: _AI text below_ :robot:" to indicate you are an agent speaking on a user's behalf.

    PR descriptions should be clear and short. Don't report test plans and checkboxes, just describe if something was done beyond running stuff that runs already in CI.
    """)
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""
    ## 💡 Claude Code tips

    * `ccstatusline` (`npx`) is great (much better than using AI to write a status line!)
    * Write a hook to check for worktrees writing to non-worktree paths and *warn* (never force in hooks)
    * Global skills can be made name-only (one at a time) - save on tokens
    * Claude can understand itself: ask it to run 20 subagents, but max at 5 at a time, and it will do it.
    * How you prompt depends on the model size:
    """),
        mo.hstack(
            [
                mo.callout(mo.md(r"""**Sonnet**

    Needs every detail"""), kind="warn"),
                mo.callout(mo.md(r"""**Opus**

    Takes a little direction"""), kind="info"),
                mo.callout(mo.md(r"""**Fable**

    Just point very gently"""), kind="success"),
            ],
            widths="equal",
            gap=1,
        ),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    # 🔍 A closer look at specific examples
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🔎 Sweeping code reviews

    (You probably knew this was coming!)

    https://iscinumpy.dev/post/claude-code-reviews

    > Review this project for bugs, performance, simplifications, and modernizations

    * Fable finds a ton, and has a really low false positive rate.
    * Opus finds some, and has a low false positive rate
    * Kimi/GLM find some, moderate false positive rate
    """)
    return


@app.cell
def review_overall_stats(mo):
    mo.hstack(
        [
            mo.stat(
                "~400",
                label="Bugs found",
                caption="plus 400+ perf/cleanup fixes",
                bordered=True,
            ),
            mo.stat(
                "30+",
                label="Projects reviewed",
                caption="mine and by request",
                bordered=True,
            ),
            mo.stat(
                "~100%",
                label="Merge rate",
                caption="on decided PRs",
                bordered=True,
            ),
            mo.stat(
                "$20\u201360",
                label="Cost per review",
                caption="Fable, comprehensive",
                bordered=True,
            ),
        ],
        widths="equal",
    )
    return


@app.cell
def review_standout(mo):
    mo.vstack([
        mo.md(r"""### 🔎 Sweeping-review finds"""),
        mo.hstack(
            [
                mo.stat(
                    "Slipped past",
                    label="CLI11 · 100% coverage",
                    caption="two flags broke only when combined (#1358)",
                    bordered=True,
                ),
                mo.stat(
                    "Data loss",
                    label="nox",
                    caption="one non-ASCII name wiped every session (#1108)",
                    bordered=True,
                ),
                mo.stat(
                    "15 bugs",
                    label="scikit-build-core",
                    caption="4 serious, on a project I wrote from scratch (#1317)",
                    bordered=True,
                ),
            ],
            widths="equal",
        ),
        mo.hstack(
            [
                mo.stat(
                    f"50% faster",
                    label="pyhs3",
                    caption=f"From 119 s to 73.4 s",
                    bordered=True,
                ),
                mo.stat(
                    f"Regression caught",
                    label="packaging",
                    caption=f"Caught before release",
                    bordered=True,
                ),
                mo.stat(
                    "Off-by-one",
                    label="pybind11",
                    caption="stale Python 2 header shifted error lines (#6089)",
                    bordered=True,
                ),
            ],
            widths="equal",
        )
    ])
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""## :package: Code review: packaging"""),
        mo.hstack(
            [
                mo.md(r"""
    [pypa/packaging#1170](https://github.com/pypa/packaging/pull/1170) Copilot read my _binary_ pickle and noticed it didn't match the comment description above

    Ironically, this was the only one I'd done by hand, and I messed it up. The others were handled by AI!
    """),
                mo.image(
                    "public/copilot_review_packaging_1170.png",
                    alt="Copilot review comment on pypa/packaging#1170",
                    width="100%",
                    rounded=True,
                ),
            ],
            widths=[1, 1],
            gap=2,
            align="start",
        ),
    ])
    return


@app.cell
def _(mo):
    _table_md = mo.md(r"""
    | Consumer | How it evaluates markers | Breaks on upgrade to this PR |
    |---|---|---|
    | pip | default-environment sites pass only `{"extra": ...}`; no platform/os/sys patch coupled to a marker evaluate in code or tests | No |
    | setuptools | default-environment sites; no platform/os/sys patch coupled to an evaluate | No |
    | pipenv | production patches `default_environment`, then evaluates with no explicit env (`PIPENV_RESOLVER_PYTHON_VERSION`) | Yes, production |
    | pex | production passes an explicit env; `tests/test_pep_508.py` reassigns `default_environment` then evaluates with no env | Yes, tests |
    | poetry-core, poetry, pdm, dep-logic, unearth, flit | own marker implementation | No |
    | build, virtualenv, tox, pip-audit | real packaging `Marker`, no platform patch coupled to an evaluate | No |
    | hatchling, cibuildwheel | pass an explicit target `environment=` | No |
    | pipdeptree | default-environment sites; its `platform` patch is in a module that evaluates no markers | No |
    | scikit-build-core | one default-environment site; its platform patches drive its own override engine, not packaging markers | No |
    | twine, conda, grayskull, conda-build, installer, importlib_metadata, dependency-groups | do not evaluate packaging markers | No |
    """)

    _small_table = mo.Html(
        "<style>.pkg-table table { font-size: 0.85rem !important; line-height: 1.3 !important; }</style>"
        f'<div class="pkg-table">{_table_md.text}</div>'
    )

    mo.hstack(
        [
            mo.md(r"""
    [pypa/packaging#1250](https://github.com/pypa/packaging/pull/1250) Claude Opus 4.8 + Ultracode tried 20 popular downstream packages against the PR that used this part of the code, and found two that broke. Oh, by the way, both _vendored_ packaging!
    """),
            _small_table,
        ],
        widths=[1, 2],
        gap=2,
        align="center",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🔀 Don't (only?) make AI do what you'd do

    ### Make AI do what you would not do
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🧪 Scikit-build-core: Testing ~20 downstream projects

    * I had a `nox -s downstream -- <...>` that can test downstream projects
    * I had Claude write a SKILL.md for testing downstream projects
        * Check with last released scikit-build-core
        * Check with current development branch scikit-build-core
        * Try editable installs too
        * Produce a report describing any regressions
    * Now I could fire off many subagents running the skill, with a max number parallel (to manage system resources)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    [scikit-build/scikit-build-core#1439](https://github.com/scikit-build/scikit-build-core/pull/1439) Summary:

    Ran it against **20 downstream projects** (`main` vs. `v0.12.2`):

    * ✅ **16 parity** — iminuit, spglib, rapidfuzz, gemmi, boost-histogram, nanobind, pyzmq, ...
    * ⚪ **2 upstream-only failures** — astyle, symusic fail identically on both sides (not us)
    * 🔴 **2 regressions discovered** in unreleased `main`:
        * **manifold3d** — a new path check hard-errors on a CMake-installed package that was previously skipped silently (fixed in [#1440](https://github.com/scikit-build/scikit-build-core/pull/1440))
        * **coreforecast** — a renamed-field warning became an aborting error for projects without a pinned `minimum-version`
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🔗 Developing against downstream

    * [pytorch/pytorch#180247](https://github.com/pytorch/pytorch/pull/180247) moves pytorch to scikit-build-core (from setuptools)
    * I asked Claude for a report on the pain points of the transition [scikit-build/scikit-build-core#1367](https://github.com/scikit-build/scikit-build-core/issues/1367)
    * I created 4-5 PRs based on this report
    * On one, I had Claude adapt the downstream PR based on my PR, and found a problem I was able to address.
    * I even added the "diff for 1.0+ support" to the upstream PR
    """)
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""## 🐛 Working through issues"""),
        mo.hstack(
            [
                mo.md(r"""
    Scikit-build-core had 140+ open issues. **Now at 20.**

    * I asked Claude to find all the reproducible bug reports
    * I asked for subagents to make fixes: 10 PRs
    * 6-7 mergable, ~2 needed extra work, 1 closed

    I asked for a [categorization](https://github.com/orgs/scikit-build/discussions/1343)

    * I used this to target work for the 1.0 release!
    """),
                mo.image(
                    "public/scikit-build-core-issue-cat.png",
                    alt="Scikit-build-core issue categorization snippet",
                    width="100%",
                    rounded=True,
                ),
            ],
            widths=[1.4, 1],
            gap=2,
            align="start",
        ),
    ])
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""
    ## 🏗️ scikit-build (classic) backend

    * Tests change due to removals (mostly `setup.py` commands)
    * Spanned three repos, including [scikit-build-sample-projects](https://github.com/scikit-build/scikit-build-sample-projects)

    Claude Fable did the conversion:

    * All the test adjustments and replacements, and tested the samples repo
    * Found and fixed **seven bugs** in scikit-build-core's setuptools plugin
        * Located my local checkout, applied fixes there, and offered a PR!
    """),
        mo.callout(
            mo.md(r"""_I was really impressed, especially at how it was happy (proactive, even) to work in multiple repos at the same time._"""),
            kind="success",
        ),
    ])
    return


@app.cell
def _(mo):
    mo.hstack(
        [
            mo.md(r"""
    ## 🎨 Beautiful Hugo

    * Made over 100 PRs in a day with GLM 5.1
    * Lots of polish
    * Updated bootstrap 3→4→5 (I tried and failed on 3→4)
    * Many requested features
    * Upstreamed additions from iscinumpy
    """),
            mo.image(
                "public/old_hugo.png",
                alt="old beautiful hugo",
                width="100%",
                rounded=True,
                caption="Before",
            ),
            mo.image(
                "public/new_hugo.png",
                alt="new beautiful hugo",
                width="100%",
                rounded=True,
                caption="After",
            ),
        ],
        widths=[1, 1, 1],
        gap=2,
        align="start",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## ⚡ GPU hackathon

    * Great for exploring a new codebase
    * Found bugs, was able to find missing terms
    * Eerily good at matching what I and the NVIDIA mentor plans
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### AI could profile and propose speedups locally.

    * For GPU, I explained that I couldn't run on the GPU node, and I copy-pasted its sample code and results back and forth (along with profiles)
    * Could predict speedups on GPU to a few percent!
    """)
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md(r"""
    A few results:

    * We could probably have accelerated GPU more; I know a lot of numba so knew to push that the most, and it was local
    * They were so happy that they could simulate scales impossible before
    * They were all using AI by the end of the session
    """),
        mo.callout(
            mo.md(r"""_"The best ad we've seen for AI is watching you use it for 30 minutes"_"""),
            kind="success",
        ),
    ])
    return


@app.cell
def _(mo):
    mo.hstack(
        [
            mo.stat(
                f"1,000x",
                label="CPU",
                caption=f"From original CPU numba version",
                bordered=True,
            ),
            mo.stat(
                f"1,000x",
                label="GPU",
                caption=f"Speedup from original version",
                bordered=True,
            ),
            mo.stat(
                f"Missing term",
                label="Jacobian",
                caption=f"Computed and solved numeric discrepancy",
                bordered=True,
            )
        ],
        justify="space-around",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🏆 Other successes

    * Solved bugs that I didn't have time to work on from up to 6 years ago
    * Made scikit-build-core's test suite 40% faster with the same coverage (Fable)
    * Reworked flake8-lazy to do one pass instead of 18, 4.5x faster, 200 LoC less (Fable)
    * Scikit-build-core editable installs bugs worked out
    * Solved flaky tests in awkward-array
    * My [projects page](https://iscinumpy.dev/page/projects/)
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 🎬 Making these slides

    * Created in marimo
    * Activated the AI bridge skill in Claude (Fable and Opus)
    * Built the json data, dropped it in, and asked for plots
    * Layout on some slides (split layout, shrink some text, etc.)
    * Summaries for a couple of issues
    * Graphical touchups (emojis, callouts, etc)
    """)
    return


if __name__ == "__main__":
    app.run()
