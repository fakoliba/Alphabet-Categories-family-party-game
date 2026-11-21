(function (root, factory) {
  const storage = factory();
  if (typeof module === "object" && module.exports) module.exports = storage;
  if (root) root.AlphabetStorage = storage;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const KEY = "alphabet-categories-save-v1";
  const emptySave = () => ({ settings: null, activeGame: null, pastGames: [] });

  function load(storage) {
    try {
      storage = storage || globalThis.localStorage;
      const parsed = JSON.parse(storage.getItem(KEY) || "null");
      if (!parsed || typeof parsed !== "object") return emptySave();
      return {
        settings: parsed.settings || null,
        activeGame: parsed.activeGame || null,
        pastGames: Array.isArray(parsed.pastGames) ? parsed.pastGames : [],
      };
    } catch {
      return emptySave();
    }
  }

  function save(data, storage) {
    storage = storage || globalThis.localStorage;
    storage.setItem(KEY, JSON.stringify(data));
  }

  return { KEY, load, save };
});
