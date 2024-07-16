import { atom, WritableAtom } from "jotai";

export function atomRequired<Value>(
  initVal?: Value | undefined,
): WritableAtom<Value, [Value], void> {
  const privateAtom = atom<Value | undefined>(initVal);

  return atom<Value, [Value], void>(
    (get) => {
      const val = get(privateAtom);
      if (val === undefined) {
        throw new Error("envAtom: env is undefined");
      }
      return val;
    },
    (_, set, newVal) => {
      set(privateAtom, newVal);
    },
  );
}
