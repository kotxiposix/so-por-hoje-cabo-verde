export function createSafeStorage(provider, onUnavailable = () => {}) {
  function useStorage(operation, fallback) {
    try {
      const storage = provider();
      if (!storage) throw new Error("Storage unavailable");
      return operation(storage);
    } catch {
      onUnavailable();
      return fallback;
    }
  }

  return {
    getItem(key) {
      return useStorage((storage) => storage.getItem(key), null);
    },
    setItem(key, value) {
      return useStorage((storage) => {
        storage.setItem(key, value);
        return true;
      }, false);
    },
    removeItem(key) {
      return useStorage((storage) => {
        storage.removeItem(key);
        return true;
      }, false);
    },
    keys() {
      return useStorage((storage) => {
        const keys = [];
        for (let index = 0; index < storage.length; index += 1) {
          const key = storage.key(index);
          if (key !== null) keys.push(key);
        }
        return keys;
      }, []);
    },
    removeWhere(predicate) {
      return useStorage((storage) => {
        const keys = [];
        for (let index = 0; index < storage.length; index += 1) {
          const key = storage.key(index);
          if (key !== null && predicate(key)) keys.push(key);
        }
        keys.forEach((key) => storage.removeItem(key));
        return true;
      }, false);
    },
  };
}
