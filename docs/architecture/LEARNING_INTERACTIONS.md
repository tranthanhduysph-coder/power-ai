# Work feedback, Tutor popup and cycle review

The Tutor launcher is a compact smiling robot icon. Pointer capture supports
mouse, pen and touch dragging; a movement threshold prevents a drag from
opening the chat. The popup header can be dragged independently. Arrow keys
move the focused launcher or header. Only launcher coordinates are stored in
localStorage (no identity or learning content). Positions are clamped when the
viewport, visual viewport or study dock changes, reserving the dock's band so
neither the launcher nor popup covers the study timer.

Work tasks remain authored per curriculum unit/language. They are not regenerated
from individual Prepare or Organize responses. Tutor receives the saved Prepare
goal, confidence, readiness and weak concepts, the Organize concept map, saved
Work evidence, and the current answer included in the explicit feedback request.
The Work prompt now explicitly asks for guidance tailored to that evidence.

Previously the Work feedback button only filled the side-chat input. It did not
send a request or reveal the field. It now sends the current task and unsaved
answer directly and opens the popup, with pending/error state in the same panel.

The Tutor popup is nonmodal, keyboard accessible (Escape minimizes and returns
focus), scrollable, responsive, and does not occupy a lesson grid column. Closing
it retains the conversation and draft while that lesson page remains open. It is
not a persistent cross-device chat history: reload/navigation resets temporary
chat state. Conversations are separated by cycle and phase and cleared with a
change of authenticated user. Successful turns, image analysis and illustration
remain supported. The last eight text turns (up to 4,000 characters each) are
passed as conversational context for follow-up questions; they are not added to
the learning-event history payload. No image data is repeated in text history.

Progress now lists the current user's cycles across lessons, with dates, phase,
completion count, paging and continue/review links. The history endpoint adds
optional summary, offset and unit filters, while preserving detailed per-unit
responses for existing lesson controls. Ownership remains enforced by user ID.

Links have the form `/learn/<unit>?session=<uuid>`. A linked cycle is fetched by
GET, never created as a fallback. Invalid, inaccessible or wrong-unit links show
an error. Starting a new cycle updates the link to the newly created ID. An older
cycle outside the ten most recent entries is included in the lesson selector
when explicitly opened. Reviewing phases does not rewind progression.

No migration, API key change, model change, new external service or production
student-data edit is needed. OpenAI configuration remains the existing Render
configuration authorized by the owner.

Validation uses a disposable, network-isolated PostgreSQL16/pgvector database,
a fake OpenAI client and a local synthetic UI API. Browser checks cover immediate
Work feedback with the current draft, one request per click, minimize/reopen,
follow-up context, visible error with retryable draft, cycle review and reload
without session creation, and popup width at the mobile breakpoint. No real
student responses are sent to OpenAI during local tests.

Launcher browser checks also cover mouse dragging without an accidental open,
click-to-open after dragging, independent header dragging, keyboard movement,
position restoration after reload, clamping on resize, and the clear timer band
at desktop, 390×844 and 740×400 viewports. Touch uses the same Pointer Events
handlers; a physical touchscreen was not part of these checks.
