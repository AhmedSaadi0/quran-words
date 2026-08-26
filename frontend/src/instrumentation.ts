/**
 * Server instrumentation hook — runs once when Next.js server starts.
 * Increases EventEmitter defaultMaxListeners to silence
 * `MaxListenersExceededWarning: 11 drain listeners added to [Gzip]` under
 * concurrent fetches (Promise.all with 4-5 API calls per page).
 * See: https://github.com/nodejs/node/issues/5108
 */
export function register() {
  try {
    // Use Function constructor to hide Node APIs from Edge static analysis
    // (Next warns "A Node.js API is used ... not supported in Edge Runtime")
    const getProcess = Function('return typeof process !== "undefined" ? process : undefined') as () =>
      | NodeJS.Process
      | undefined;
    const proc = getProcess();
    if (proc?.setMaxListeners) proc.setMaxListeners(20);

    const getEvents = Function('return typeof require !== "undefined" ? require("events") : undefined') as () =>
      | { EventEmitter: { defaultMaxListeners: number } }
      | undefined;
    const events = getEvents();
    if (events) events.EventEmitter.defaultMaxListeners = 20;
  } catch {
    // ignore in edge runtime
  }
}
