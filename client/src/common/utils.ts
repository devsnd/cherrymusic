export function enumerate (iterable: Array<any>) {
    const retval = [];
    let idx = 0;
    for (const elem of iterable) {
        retval.push([idx, elem]);
        idx++;
    }
    return retval;
}

export function zPad (num: number, digits: number) {
    let numStr = '' + num;
    while (numStr.length < digits) {
        numStr = '0' + numStr;
    }
    return numStr;
}

export function formatDuration (duration: number) {
    duration = Math.round(duration);
    const secs = duration % 60;
    const mins = ((duration / 60) % 60) | 0;
    const hrs = ((duration / 3600) % 60) | 0;
    if (hrs) {
        return `${hrs}:${zPad(mins, 2)}:${zPad(secs, 2)}`;
    }
    return `${mins}:${zPad(secs, 2)}`;
}

export function randomId () {
  return Math.random().toString(36).substr(2, 10);
}

export function sum (list: Array<number>) {
  return list.reduce((accu, elem) => accu + elem, 0);
}

export function avg (list: Array<number>) {
  if (list.length === 0) {
    return null;
  }
  return sum(list) / list.length;
}

export function any (args: Array<boolean>) {
  for (const arg of args) {
    if (arg) {
      return true;
    }
  }
  return false;
}

export function all (args: Array<boolean>) {
  for (const arg of args) {
    if (!arg) {
      return false;
    }
  }
  return true;
}

export function dict (keyValPairs: any[]) {
  let retval: {[key: string]: any} = {};
  for (const keyVal of keyValPairs) {
    if (Array.isArray(keyVal)) {
      retval[keyVal[0]] = keyVal[1];
    } else {
      retval = {...retval, ...keyVal};
    }
  }
  return retval;
}
