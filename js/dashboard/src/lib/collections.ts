type SeparatorGenFunc<E, S> = (elem: E, index: number) => S;

/**
 * injectSeparators takes an array and then inserts a separator between its elements.
 *
 * @param arr
 * @param separator
 * @returns
 */
function injectSeparators<E, S>(arr: Array<E>, separator: S): Array<E | S> {
  return injectSeparatorsDynamic(arr, () => separator);
}

function injectSeparatorsDynamic<E, S>(
  arr: Array<E>,
  separator: SeparatorGenFunc<E, S>,
): Array<E | S> {
  const newArr = new Array<E | S>(Math.max(arr.length * 2 - 1, 0));
  for (let i = 0; i < arr.length - 1; i++) {
    newArr[i * 2] = arr[i];
    newArr[i * 2 + 1] = separator(arr[i], i);
  }
  if (arr.length > 0) {
    newArr[newArr.length - 1] = arr[arr.length - 1];
  }
  return newArr;
}

class DefaultMap<K, V> extends Map<K, V> {
  private defaultValue: (key: K) => V;

  constructor(
    defaultValue: (key: K) => V,
    entries?: ReadonlyArray<[K, V]> | null,
  ) {
    super(entries);
    this.defaultValue = defaultValue;
  }

  get(key: K): V {
    if (!this.has(key)) {
      this.set(key, this.defaultValue(key));
    }
    return super.get(key)!;
  }
}

export class RequiredMap<K, V> extends Map<K, V> {
  get(key: K): V {
    if (!this.has(key)) {
      throw new Error(`Key '${key}' does not exist in RequiredMap`);
    }
    return super.get(key)!;
  }
}

export { injectSeparators, injectSeparatorsDynamic, DefaultMap };
