/* Duo icon set
   The canonical interface icons for every lesson in a teach-duo workspace.

   These are inline SVG, never emoji. Emoji render differently on every
   platform, fall back to monochrome or to a mismatched colour on coloured
   surfaces, and cannot be recoloured by the design system. Inline SVG uses
   currentColor, so the tokens in duo.css decide how each icon looks.

   Shared geometry: 24x24 viewBox, 2px stroke, round caps and joins, so every
   icon carries the same optical weight. A filled icon sets fill on the path
   and CSS can override it, which is how a spent heart becomes an outline.
*/
(function (global) {
  "use strict";

  function svg(body, extra) {
    return (
      '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
      'stroke-linejoin="round"' + (extra || "") + ">" + body + "</svg>"
    );
  }

  var ICONS = {
    /* Restart, top bar left. */
    close: svg('<path d="M6 6 L18 18"/><path d="M18 6 L6 18"/>'),

    /* A heart. Filled while alive; CSS drops the fill when it is lost. */
    heart: svg(
      '<path fill="currentColor" stroke="none" ' +
      'd="M12 20.6 C12 20.6 3.2 15.1 3.2 9.3 A4.75 4.75 0 0 1 12 6.7 ' +
      'A4.75 4.75 0 0 1 20.8 9.3 C20.8 15.1 12 20.6 12 20.6 Z"/>'
    ),

    /* XP. */
    zap: svg(
      '<path fill="currentColor" stroke="none" ' +
      'd="M13.4 2 L4.6 13.6 H10.4 L9.6 22 L19.4 10.2 H13.4 Z"/>'
    ),

    /* Lesson complete. */
    trophy: svg(
      '<path d="M7 3 H17 V9.5 A5 5 0 0 1 7 9.5 Z" fill="currentColor" stroke="none"/>' +
      '<path d="M7 4.5 H4.4 V6.8 A3.4 3.4 0 0 0 7.3 10.2"/>' +
      '<path d="M17 4.5 H19.6 V6.8 A3.4 3.4 0 0 1 16.7 10.2"/>' +
      '<path d="M12 14.5 V18"/>' +
      '<path d="M8.6 21 H15.4 L14 18 H10 Z" fill="currentColor" stroke="none"/>'
    ),

    /* Sound on. */
    volumeOn: svg(
      '<path d="M4 9.4 H7 L11.4 5.8 V18.2 L7 14.6 H4 Z" fill="currentColor" stroke="none"/>' +
      '<path d="M15 9.6 A3.4 3.4 0 0 1 15 14.4"/>' +
      '<path d="M17.6 7 A7 7 0 0 1 17.6 17"/>'
    ),

    /* Sound muted. */
    volumeOff: svg(
      '<path d="M4 9.4 H7 L11.4 5.8 V18.2 L7 14.6 H4 Z" fill="currentColor" stroke="none"/>' +
      '<path d="M15.6 9.8 L20.4 14.4"/>' +
      '<path d="M20.4 9.8 L15.6 14.4"/>'
    ),

    /* Link out, used by the primary source line. */
    external: svg(
      '<path d="M14 4 H20 V10"/>' +
      '<path d="M20 4 L11 13"/>' +
      '<path d="M18 14.5 V19 A1.5 1.5 0 0 1 16.5 20.5 H5 A1.5 1.5 0 0 1 3.5 19 V7.5 ' +
      'A1.5 1.5 0 0 1 5 6 H9.5"/>'
    ),

    /* Next lesson or reference link. */
    arrowRight: svg('<path d="M5 12 H19"/><path d="M13 6 L19 12 L13 18"/>')
  };

  /* Fill every [data-icon] slot on the page from the set above, so markup
     declares which icon it wants by name and never hard-codes a glyph. */
  function hydrate(root) {
    var scope = root || global.document;
    if (!scope || !scope.querySelectorAll) return;
    scope.querySelectorAll("[data-icon]").forEach(function (slot) {
      var name = slot.getAttribute("data-icon");
      if (ICONS[name] && !slot.firstChild) {
        slot.innerHTML = ICONS[name];
      }
    });
  }

  global.DuoIcons = {
    icons: ICONS,
    get: function (name) {
      return ICONS[name] || "";
    },
    hydrate: hydrate,
    names: Object.keys(ICONS)
  };
})(typeof window !== "undefined" ? window : globalThis);