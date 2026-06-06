const collectionButtons = document.querySelectorAll("[data-collection]");
const menuToggle = document.querySelector("#menu-toggle");
const siteMenu = document.querySelector("#site-menu");
const collectionPanels = {
  sobriu: document.querySelector("#collection-sobriu"),
  spirit: document.querySelector("#collection-spirit"),
};

if (menuToggle && siteMenu) {
  menuToggle.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("menu-open");
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    menuToggle.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
  });

  siteMenu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      document.body.classList.remove("menu-open");
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.setAttribute("aria-label", "Abrir menu");
    });
  });
}

collectionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const selected = button.dataset.collection;
    collectionButtons.forEach((item) => {
      const isActive = item === button;
      item.classList.toggle("active", isActive);
      item.setAttribute("aria-selected", String(isActive));
    });
    Object.entries(collectionPanels).forEach(([key, panel]) => {
      panel.hidden = key !== selected;
    });
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
  group.querySelectorAll(".media-card").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");

  iframe.src = value.startsWith("videoseries")
    ? `https://www.youtube.com/embed/${value}`
    : `https://www.youtube.com/embed/${value}`;
}
