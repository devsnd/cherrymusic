
export function injectCSS (css: string) {
    /* adapted from https://stackoverflow.com/a/524721/1191373 */
    const head = document.head || document.getElementsByTagName('head')[0];
    const styleNode = document.createElement('style');
    styleNode.type = 'text/css';
    styleNode.appendChild(document.createTextNode(css));
    head.appendChild(styleNode);
}
