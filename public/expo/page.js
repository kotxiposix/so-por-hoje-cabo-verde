const collectionButtons = document.querySelectorAll("[data-collection]");
const menuToggle = document.querySelector("#menu-toggle");
const siteMenu = document.querySelector("#site-menu");
const mobileMenuMedia = window.matchMedia("(max-width: 760px)");
const collectionPanels = {
  sobriu: document.querySelector("#collection-sobriu"),
  spirit: document.querySelector("#collection-spirit"),
};

function setMenuOpen(isOpen, options = {}) {
  const { focusMenu = false, restoreFocus = false } = options;
  document.body.classList.toggle("menu-open", isOpen);
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
  siteMenu.inert = mobileMenuMedia.matches && !isOpen;
  if (focusMenu) siteMenu.querySelector("a")?.focus();
  if (restoreFocus) menuToggle.focus();
}

function syncMenuMode() {
  if (!mobileMenuMedia.matches) {
    document.body.classList.remove("menu-open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Abrir menu");
    siteMenu.inert = false;
    return;
  }
  siteMenu.inert = !document.body.classList.contains("menu-open");
}

if (menuToggle && siteMenu) {
  syncMenuMode();
  menuToggle.addEventListener("click", () => {
    const isOpen = !document.body.classList.contains("menu-open");
    setMenuOpen(isOpen, { focusMenu: isOpen });
  });

  siteMenu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      setMenuOpen(false);
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.classList.contains("menu-open")) {
      event.preventDefault();
      setMenuOpen(false, { restoreFocus: true });
    }
  });
  mobileMenuMedia.addEventListener("change", syncMenuMode);
}

function selectCollection(button, options = {}) {
  const selected = button.dataset.collection;
  collectionButtons.forEach((item) => {
    const isActive = item === button;
    item.classList.toggle("active", isActive);
    item.setAttribute("aria-selected", String(isActive));
    item.tabIndex = isActive ? 0 : -1;
  });
  Object.entries(collectionPanels).forEach(([key, panel]) => {
    panel.hidden = key !== selected;
  });
  if (options.focus) button.focus();
}

collectionButtons.forEach((button, index) => {
  button.addEventListener("click", () => selectCollection(button));
  button.addEventListener("keydown", (event) => {
    const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + collectionButtons.length) % collectionButtons.length;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % collectionButtons.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = collectionButtons.length - 1;
    selectCollection(collectionButtons[nextIndex], { focus: true });
  });
});

document.querySelectorAll("[data-video]").forEach((button) => {
  button.addEventListener("click", () => {
    selectMedia(button, "#video-player", "video");
  });
});

document.querySelectorAll("[data-podcast]").forEach((button) => {
  button.addEventListener("click", () => {
    selectMedia(button, "#podcast-player", "podcast");
  });
});

function selectMedia(button, iframeSelector, dataKey) {
  const iframe = document.querySelector(iframeSelector);
  const value = button.dataset[dataKey];
  if (!iframe || !value) return;

  const group = button.closest("[data-media-gallery]");
  group.querySelectorAll(".media-card[data-video], .media-card[data-podcast]").forEach((item) => {
    const isActive = item === button;
    item.classList.toggle("active", isActive);
    item.setAttribute("aria-pressed", String(isActive));
  });

  iframe.src = `https://www.youtube-nocookie.com/embed/${value}`;
  iframe.title = button.textContent.replace(/\s+/g, " ").trim();
}
