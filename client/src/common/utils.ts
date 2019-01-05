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
