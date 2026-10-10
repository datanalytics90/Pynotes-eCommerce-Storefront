// Lightweight progressive enhancement for the storefront UI.
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-ajax-cart]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const response = await fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
      });
      if (response.ok) {
        const data = await response.json();
        document.querySelectorAll("[data-cart-count]").forEach((el) => {
          el.textContent = data.total_items;
        });
      }
    });
  });
});
