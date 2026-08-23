Location Story Engine — Version 0.5 Experience Upgrade

## Status: Partially implemented

- ✅ **Item 12–17 (Actual Image Export)** — done. `apps/web/src/main.tsx`'s Export Image
  button reuses the backend's export-validation boundary (`POST /projects/{id}/export`),
  then captures the live MapLibre canvas client-side (`canvasContextAttributes.preserveDrawingBuffer`)
  and composites story points on top, downloading a real PNG. Matches this doc's guidance
  in §15 (canvas preservation) and §13 (browser-side over server rendering-farm).
- ✅ **Item 2–6 (Intent-driven category interpretation)** — done.
  `POST /intent/interpret` (`services/api/app/intent_interpreter.py`) sends the user's free
  text plus the supported category id list to Claude, gets back `{summary, categories}`,
  and filters `categories` to the supported set server-side (unknown model output can't
  leak into search). Frontend: **Build map from this intent** button (needs intent text +
  a subject point) runs the interpreted categories through the existing nearby-search
  loop and shows "Map focus: …" near the intent field, in plain language per this doc's
  §6 guidance. `useMyLocation` also uses this — if the user already typed an intent before
  clicking it, that intent now drives category selection instead of being overwritten and
  falling back to a fixed default set (a bug this fix also caught). Category registry grew
  from 7 to 11 ids to actually cover common asks: added `healthcare`, `entertainment`,
  `shopping`, `community`.
- ❌ **Item 7–11 (Category-aware icon markers + legend)** — not started. Markers are still
  flat colored dots (`SYMBOL_COLORS` in `main.tsx`, now 11 colors), no icon library, no legend.
- ❌ **Item 18–23 (Layout/navigation polish)** — not started. Sidebar is still one long
  scrolling form; no header/nav, no centered pre-map setup card.

Everything else in this document (below) remains the target spec for the unimplemented items.

Intent / Goal

Upgrade the existing Location Story Engine from the current working MVP into a more compelling Version 0.5 experience without redesigning the architecture or expanding into future intelligence features.

The application already supports:

* location lookup,
* nearby-place discovery,
* editable story points,
* Anthropic-generated relocation narrative,
* project save/reload,
* category and symbol fields,
* an export validation boundary.

This intent must make the existing application feel intentionally AI-driven, visually expressive, exportable, and professionally presented.

The four required improvements are:

1. Make the user’s plain-language map intent actually influence the map.
2. Render category-specific map symbols rather than nearly identical dots.
3. Add a working PNG/JPEG export button directly to the main experience.
4. Improve layout, navigation, hierarchy, and polish without redesigning the product.

Use the smallest safe change required to accomplish these goals.

⸻

1. Current State / Repo Reality

Inspect the repository before modifying anything.

Relevant existing areas include:

* apps/web/src/main.tsx
* apps/web/src/styles.css
* services/api/app/main.py
* services/api/app/narrative.py
* services/api/app/models.py
* existing contracts, hooks, tests, and intent files.

Do not assume the repository still exactly matches this document.

Use the repository itself as source of truth.

Preserve working behavior unless this intent explicitly changes it.

⸻

2. Intent Must Drive the Map

Problem

The main UI asks:

“What story are you trying to tell?”

That field currently captures useful user intent, but the initial map-generation behavior is largely predetermined.

For example, the application can currently fetch nearby categories such as:

* coffee,
* restaurants,
* schools,
* parks,
* transit,
* hotels,
* grocery.

However, the automatic flow does not meaningfully interpret the user’s intent when deciding what categories matter.

This makes the intent field feel disconnected from the actual map.

Required Behavior

Introduce a small Anthropic-backed intent interpretation step.

The user should be able to enter something such as:

Show why this is a great place for a young family that likes parks, schools, restaurants, and easy access to shopping.

or:

Show why this location would be good for a business traveler who wants hotels, restaurants, coffee, and transportation nearby.

The application should interpret that request and return a small structured result.

Example conceptual contract:

{
  "summary": "Family-oriented residential location story",
  "categories": [
    "school",
    "park",
    "grocery",
    "restaurant"
  ]
}

Do not make the LLM responsible for geographic facts.

AI determines what to look for.

Existing deterministic geocoding/place-search services determine what actually exists and where it is.

⸻

3. Intent Interpretation Contract

Create or reuse an appropriate structured contract.

Preferred shape:

type InterpretedMapIntent = {
  summary: string;
  categories: string[];
};

Use the repository’s established contract conventions if equivalents already exist.

The permitted categories must come from the application’s supported category registry.

Do not allow arbitrary model-generated categories to silently enter geographic search.

Normalize model output against supported categories.

Unknown categories should be ignored or mapped safely.

⸻

4. Intent API

Add the smallest appropriate backend capability for interpreting map intent.

Conceptually:

POST /intent/interpret

or another route consistent with current API conventions.

Input:

{
  "intent": "Show why this would be a great home for a family..."
}

Output:

{
  "summary": "Family-oriented residential story",
  "categories": ["school", "park", "grocery", "restaurant"]
}

Use the existing Anthropic configuration and SDK patterns already present in the repository.

Do not add another AI provider.

Do not add another agent framework.

Do not introduce an autonomous agent.

One bounded model call is sufficient.

Prefer low-cost / low-effort inference appropriate for a small classification task.

⸻

5. Connect Intent to Map Generation

The intent interpretation must visibly affect the application.

When the user has:

1. entered an intent, and
2. selected/searched a subject address or used their location,

the system should use interpreted categories when automatically retrieving nearby points.

Do not continue automatically using the same hard-coded category set when a useful interpreted category list exists.

Example:

Intent:
"Show me why this is great for a family with children."
Possible selected categories:
Schools
Parks
Grocery
Restaurants

Example:

Intent:
"Show why this is convenient for business travel."
Possible selected categories:
Hotels
Restaurants
Coffee
Transit

Keep the existing manual category buttons.

AI suggestions should augment user control, not replace it.

⸻

6. Make the AI Behavior Visible

The user should be able to tell that their intent mattered.

Near the intent field or map controls, show a compact UI such as:

Map focus
Schools • Parks • Grocery • Restaurants

or:

AI selected:
School
Park
Grocery
Restaurant

Avoid technical language such as:

* LLM,
* Anthropic request,
* model output,
* inference,
* tokens.

The experience should communicate:

“I understood what kind of map you wanted.”

not:

“An AI API was called.”

Allow the user to add/remove category selections before or after points are retrieved if this can be done with minimal change.

⸻

7. Category-Aware Marker System

Problem

Existing story points contain:

* category,
* symbol,
* label,
* coordinates.

The frontend also already has category/color concepts.

However, markers are visually too similar.

Required Behavior

Create a reusable marker definition registry.

Example conceptual structure:

const MARKER_DEFINITIONS = {
  subject: {
    icon: "home",
    color: "...",
    size: 32
  },
  coffee: {
    icon: "coffee",
    color: "...",
    size: 24
  },
  restaurant: {
    icon: "utensils",
    color: "...",
    size: 24
  },
  school: {
    icon: "graduation-cap",
    color: "...",
    size: 24
  },
  park: {
    icon: "trees",
    color: "...",
    size: 24
  },
  transit: {
    icon: "bus",
    color: "...",
    size: 24
  },
  hotel: {
    icon: "bed",
    color: "...",
    size: 24
  },
  grocery: {
    icon: "shopping-cart",
    color: "...",
    size: 24
  },
  company: {
    icon: "building",
    color: "...",
    size: 24
  },
  employer: {
    icon: "briefcase",
    color: "...",
    size: 24
  },
  golf: {
    icon: "flag",
    color: "...",
    size: 24
  },
  custom: {
    icon: "map-pin",
    color: "...",
    size: 24
  }
};

Exact implementation may vary.

⸻

8. Symbol Library

Before adding a dependency, inspect the existing frontend dependencies.

If an icon library is already available, reuse it.

Otherwise choose one lightweight, well-maintained library compatible with React and the existing build.

Good candidates include a simple SVG icon library such as Lucide if no equivalent already exists.

Do not introduce a large UI framework merely to obtain icons.

SVG or DOM-based markers are acceptable.

No remote icon service should be required.

⸻

9. Marker Visual Requirements

Markers must be visually distinguishable by more than color.

A user should be able to distinguish categories even if the map is printed or viewed quickly.

Use:

* icon,
* color,
* and optionally modest size differences.

The subject property/location should remain the strongest visual anchor.

Example:

HOME        larger primary marker
SCHOOL      graduation-cap
PARK        tree
COFFEE      cup
RESTAURANT  utensils
HOTEL       bed
TRANSIT     bus/train
GROCERY     cart
COMPANY     building

Keep markers readable at ordinary map zoom levels.

Avoid oversized cartoon markers.

Aim for a clean professional real-estate / location-intelligence aesthetic.

⸻

10. Marker Editing

Preserve existing ability to modify a point’s symbol.

Improve the selector if practical so the user can understand what they are choosing.

Prefer:

☕ Coffee
🌳 Park
🎓 School

or equivalent SVG/icon treatment rather than raw implementation identifiers alone.

Category and symbol should remain persisted according to existing contracts.

Do not break saved projects.

⸻

11. Marker Legend

Add a small map legend when more than one category exists.

Example:

● Home
☕ Coffee
🎓 Schools
🌳 Parks

Use the actual marker symbols, not generic dots if possible.

The legend should reflect categories currently displayed.

Keep it compact.

It may sit over the map or beside it depending on the improved layout.

⸻

12. Actual Image Export

Problem

The backend currently has an export-validation boundary but the user does not receive an actual image artifact.

Version 0.5 requires a usable image export.

Required User Experience

Add an obvious main-page action:

Export Map

or:

Download Map

Place it with primary story actions.

The user should not have to find a hidden menu.

⸻

13. Version 0.5 Export Scope

For this version, prioritize working browser-side export over production rendering infrastructure.

Required:

* PNG export.

Optional if trivial:

* JPEG export.

A browser-side implementation is acceptable for Version 0.5 provided it reliably captures:

* map,
* category markers,
* visible labels if currently rendered,
* legend if practical,
* current viewport.

Do not build a server-side 4K rendering farm.

Do not add headless Chrome infrastructure unless absolutely required.

Do not implement PDF or PowerPoint.

⸻

14. Export Quality

Produce the highest reasonable resolution from the existing browser map.

Where technically safe, render/export above CSS display resolution using device pixel ratio or an equivalent scaling technique.

Goal:

A user should be able to export an image that looks crisp enough to:

* email,
* place into a document,
* put into a presentation,
* print at ordinary sizes.

This is not yet the final production print renderer.

That belongs in a later version.

⸻

15. Map Rendering Caveat

MapLibre/WebGL canvas exporting can be affected by:

* canvas preservation,
* cross-origin tiles,
* raster tile permissions,
* browser restrictions.

Inspect the current map configuration before choosing implementation.

Use the smallest reliable approach compatible with the currently configured tile provider.

If necessary, configure MapLibre with the appropriate canvas-preservation setting.

Do not violate tile-provider licensing or terms.

If JPEG support complicates the implementation, complete PNG first.

PNG is the Version 0.5 required format.

⸻

16. Export Validation

Reuse the existing export validation boundary where appropriate.

Before allowing export, validate that the story has at least:

* an intent,
* a valid subject/location,
* exportable visible points.

Do not duplicate validation logic unnecessarily.

If backend validation already exists, call/reuse it.

Then perform browser rendering/download.

Avoid building a second conflicting export model.

⸻

17. Export Filename

Use a friendly deterministic filename.

Example:

location-story-wylie-tx.png

or:

{project-name}-map.png

Sanitize unsafe filename characters.

⸻

18. UI / Navigation Improvement

Goal

Improve the first-screen experience so it looks like a professional product rather than a development form beside a map.

Do not redesign the entire brand.

Do not add a full design system.

Improve the existing layout.

⸻

19. Recommended Desktop Layout

Prefer a structure similar to:

----------------------------------------------------------
 Location Story                       Save   Export
----------------------------------------------------------
        Tell us the story you want this map to show
        [                                      ]
        [           intent textarea            ]
        [                                      ]
        Find your subject location
        [ address / place                         ] [Find]
----------------------------------------------------------
 Map Controls / Suggested Categories
----------------------------------------------------------
              LARGE INTERACTIVE MAP
                           [legend]
----------------------------------------------------------
 Story Points / Edit Details
----------------------------------------------------------

Exact layout is up to implementation.

The key requirement is clearer hierarchy.

⸻

20. Form Positioning

The initial intent/location form should feel centered and deliberate.

Do not leave every control permanently stacked in one long narrow sidebar if a better minimal layout is possible.

A practical approach:

Before subject location exists

Show a centered setup card:

1. Project/story name
2. What story are you trying to tell?
3. Address/location
4. Use my location
5. Build / Find location

After map exists

Transition naturally into:

* map as primary canvas,
* compact controls,
* editable points panel.

Do not introduce unnecessary routing/state machines solely for this transition.

Conditional layout in the existing React application is sufficient.

⸻

21. Navigation

Add a small professional header.

Suggested items:

Location Story
New Story
Save
Export

Only include actions that actually work.

Do not create dead navigation.

If authentication/account navigation is already supported, preserve it.

Do not build new account management for this intent.

⸻

22. Visual Polish

Improve:

* spacing,
* typography,
* hierarchy,
* button consistency,
* panel/card treatment,
* responsive behavior,
* empty states,
* loading states,
* disabled states.

Use the existing CSS architecture unless there is a compelling reason not to.

Do not install Tailwind, Material UI, Bootstrap, or another major UI framework solely for this change.

⸻

23. Mobile / Responsive Behavior

Version 0.5 should remain usable on smaller screens.

Desktop may use:

controls | map

Mobile should stack logically:

controls
map
story points

Buttons must remain tappable.

Map must remain usable.

Export should still be accessible.

⸻

24. Architecture Posture

Use the minimum sufficient architecture.

Goal-oriented work

Use ordinary goal-oriented implementation for:

* UI polish,
* marker rendering,
* legend,
* layout,
* export button,
* icon registry.

Procedural boundaries

Use deterministic procedural handling only where necessary:

* Anthropic API call,
* geocoding,
* nearby-place search,
* validation,
* export,
* file download.

Do not add an orchestrator.

Do not add a multi-agent workflow.

Do not add subagents to runtime behavior.

Do not introduce queues or event buses.

⸻

25. AI Boundary

AI may:

* interpret the user’s plain-language story,
* choose relevant supported categories,
* produce a short map-focus summary.

AI may NOT:

* invent coordinates,
* invent nearby places,
* invent distances,
* fabricate amenities,
* place markers without deterministic geographic evidence.

Pattern:

User Intent
    ↓
Anthropic
    ↓
Supported Category Intent
    ↓
Deterministic Nearby Search
    ↓
Verified Places + Coordinates
    ↓
Map

This separation is mandatory.

⸻

26. Context Passing

Pass minimum sufficient context to Anthropic.

Intent interpretation needs approximately:

{
  "userIntent": "...",
  "supportedCategories": [...]
}

Do not send:

* entire project history,
* raw application state,
* coordinates,
* conversation history,
* unnecessary point data.

Use structured output.

Validate before consuming.

⸻

27. Category Registry

Avoid maintaining unrelated category definitions in multiple files if the current implementation is already drifting.

Create or reuse one clear source of category metadata for the frontend.

It should provide enough information for:

* display label,
* icon,
* marker color,
* default size,
* category identifier.

Example concept:

type CategoryDefinition = {
  id: string;
  label: string;
  icon: IconType;
  color: string;
  size: number;
};

Do not over-generalize this into a plugin system.

Version 0.5 only needs a clean registry.

⸻

28. Preserve Existing Features

The following must continue working:

* Use My Location
* address/place search
* map clicking
* nearby-category buttons
* point editing
* point removal
* point notes
* save
* reload
* relocation narrative
* existing category search
* existing validation

Do not break the current vertical slice while improving it.

⸻

29. Acceptance Criteria

Version 0.5 is successful when the following scenario works.

Scenario A — Intent-Driven Family Map

User enters:

Show why this home would work for a family that wants great access to schools, parks, groceries, and restaurants.

User supplies a subject location.

System interprets the intent.

UI visibly shows relevant categories.

Nearby searches are performed using those supported categories.

Verified locations appear on the map.

Schools have a school-oriented symbol.

Parks have a park-oriented symbol.

Restaurants have a restaurant-oriented symbol.

Grocery locations have a grocery-oriented symbol.

The subject property is visually distinct.

A legend identifies the displayed categories.

⸻

Scenario B — Different Intent, Different Map

User enters:

Show why this is convenient for a business traveler who values hotels, coffee, restaurants, and transportation.

The resulting suggested categories should meaningfully differ from Scenario A.

The application should not automatically default to the same fixed family-oriented categories.

⸻

Scenario C — Export

User builds a valid map.

User clicks:

Export Map

Browser downloads a valid PNG.

Opening that PNG shows:

* the expected map viewport,
* category-specific markers,
* subject marker,
* useful map content.

The export does not require developer tooling.

⸻

Scenario D — Existing Story

Load an existing project.

Existing points still render.

Unknown/legacy symbols safely fall back to the custom/default marker.

Saving still works.

Narrative generation still works.

⸻

30. Validation / Evidence

Before declaring completion, provide evidence for:

Backend

* intent interpreter accepts user intent,
* supported categories are constrained,
* malformed model output is rejected or safely handled,
* Anthropic errors produce useful API responses.

Frontend

* category icons render,
* category colors render,
* subject marker remains distinct,
* legend reflects visible categories,
* interpreted categories visibly affect map generation,
* manual categories remain usable,
* export button produces a PNG,
* existing saved project can reload.

Existing Tests

Run all existing backend tests.

Run the frontend build.

Fix regressions introduced by this change.

⸻

31. Suggested Tests

Add focused tests rather than building a huge test framework.

At minimum:

intent interpretation → valid supported categories
intent interpretation → unknown category rejected/ignored
legacy symbol → default marker
category registry → supported category metadata exists
export validation → invalid project rejected

Add frontend tests only where the current repository already has a suitable testing setup.

Do not introduce a large testing framework solely for this intent.

⸻

32. Implementation Sequence

Implement in this order unless repository evidence suggests a safer order:

1. Inspect repo and existing category/export/AI patterns.
2. Create/refine category registry.
3. Upgrade category-specific marker rendering.
4. Add legend.
5. Add structured intent interpretation endpoint.
6. Connect intent result to category selection.
7. Update automatic nearby search to use interpreted categories.
8. Add export implementation.
9. Add header/navigation/layout polish.
10. Improve responsive behavior.
11. Run backend tests.
12. Run frontend build/tests.
13. Manually verify the four acceptance scenarios.
14. Report implementation evidence.

⸻

33. Non-Goals

Do NOT implement in Version 0.5:

* demographics,
* crime scoring,
* school ratings,
* property valuation,
* traffic modeling,
* employment intelligence,
* parcel data,
* high-resolution server-side rendering,
* PDF generation,
* PowerPoint generation,
* billing,
* payments,
* autonomous research agents,
* multi-agent workflows,
* new authentication architecture,
* new database architecture,
* broad AWS infrastructure changes.

Those belong to later versions.

⸻

34. Stop Conditions

Stop and report rather than expanding scope if:

* working map export requires a significant rendering service,
* tile-provider restrictions make browser export impossible,
* the Anthropic configuration is unavailable,
* the proposed change requires replacing MapLibre,
* existing contracts would need a broad breaking migration,
* changes would require major architecture unrelated to this intent.

When stopped, identify the exact blocker and propose the smallest next vertical slice.

⸻

35. Delivery Expectations

Claude Code should implement the changes, not merely produce recommendations.

At completion provide:

VERSION 0.5 IMPLEMENTATION SUMMARY
Intent interpretation:
- ...
Map markers:
- ...
Export:
- ...
UX:
- ...
Files changed:
- ...
Tests/build:
- ...
Manual scenarios verified:
- ...
Known limitations:
- ...
Recommended Version 0.6:
- ...

Do not claim completion without evidence.

⸻

Final Definition of Done

Version 0.5 is done when a user can:

Describe the map they want
        ↓
Choose/find a subject location
        ↓
Have the intent influence relevant map categories
        ↓
See real verified locations
        ↓
Immediately understand categories from their symbols
        ↓
Edit the story
        ↓
Save it
        ↓
Generate the existing AI narrative
        ↓
Export the visible map as a usable PNG

The result should feel like the same application becoming a real product, not a new application being built around it.

The biggest improvement in there is the first one. Right now you’ve got AI in the product, but it happens after the map is built when you hit “Give me a reason to move here.”  This v0.5 makes the architecture much more compelling: intent → AI decides what matters → deterministic search finds the real places → category-specific map tells the story → export. That is much closer to what the Location Story Engine was supposed to be.
