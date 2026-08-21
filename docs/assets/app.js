(function () {
  "use strict";

  function formatCurrency(value) {
    var rounded = Math.round(Number(value || 0) / 1000) * 1000;
    return new Intl.NumberFormat("en-AU", {
      style: "currency",
      currency: "AUD",
      maximumFractionDigits: 0,
    }).format(rounded);
  }

  function formatNumber(value) {
    return new Intl.NumberFormat("en-AU").format(Number(value || 0));
  }

  function inventoryCard(item) {
    var title = item.year + " " + item.brand + " " + item.model;
    return (
      '<article class="inventory-card">' +
      '<a href="/inventory/' +
      item.slug +
      '/">' +
      '<div class="inventory-image-wrap">' +
      '<img src="' +
      item.image +
      '" alt="' +
      title.replace(/"/g, "&quot;") +
      '" loading="lazy" />' +
      "</div>" +
      '<div class="inventory-card-body">' +
      '<p class="inventory-meta">' +
      item.year +
      " " +
      item.brand +
      "</p>" +
      "<h3>" +
      item.model +
      "</h3>" +
      '<p class="inventory-price">' +
      formatCurrency(item.price) +
      " <span>&middot; " +
      formatNumber(item.kilometres) +
      " km</span></p>" +
      "</div>" +
      "</a>" +
      "</article>"
    );
  }

  function setupInventoryBrowser() {
    var dataNode = document.getElementById("inventory-data");
    var searchInput = document.getElementById("inventory-search");
    var sortSelect = document.getElementById("inventory-sort");
    var grid = document.getElementById("inventory-grid");
    var countNode = document.getElementById("inventory-count");

    if (!dataNode || !searchInput || !sortSelect || !grid || !countNode) {
      return;
    }

    var inventory = [];
    try {
      inventory = JSON.parse(dataNode.textContent || "[]");
    } catch (error) {
      inventory = [];
    }

    function render() {
      var query = searchInput.value.trim().toLowerCase();
      var sort = sortSelect.value;
      var filtered = inventory.filter(function (item) {
        if (!query) return true;
        var text = [
          item.title,
          item.brand,
          item.model,
          item.chassis,
          item.stockNumber,
        ]
          .join(" ")
          .toLowerCase();
        return text.indexOf(query) > -1;
      });

      filtered.sort(function (a, b) {
        if (sort === "price-asc") return a.price - b.price;
        if (sort === "price-desc") return b.price - a.price;
        if (sort === "km") return a.kilometres - b.kilometres;
        if (a.year !== b.year) return b.year - a.year;
        return a.price - b.price;
      });

      grid.innerHTML = filtered.map(inventoryCard).join("");
      countNode.textContent =
        filtered.length +
        " motorhome" +
        (filtered.length === 1 ? "" : "s");
    }

    searchInput.addEventListener("input", render);
    sortSelect.addEventListener("change", render);
    render();
  }

  function setupEnquiryForms() {
    var forms = document.querySelectorAll(".js-enquiry-form");
    forms.forEach(function (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        var data = new FormData(form);
        var name = String(data.get("name") || "").trim();
        var email = String(data.get("email") || "").trim();
        var mobile = String(data.get("sms") || "").trim();
        var message = String(data.get("message") || "").trim();
        if (!name || !email || !mobile) {
          return;
        }

        var to = form.getAttribute("data-email") || "";
        var listingTitle = form.getAttribute("data-listing-title") || "";
        var subject = listingTitle
          ? "Motorhome enquiry: " + listingTitle
          : "Used motorhome enquiry - Brisbane";

        var bodyParts = [
          "Name: " + name,
          "Email: " + email,
          "SMS / mobile: " + mobile,
          listingTitle ? "Motorhome: " + listingTitle : null,
          message ? "Message:\n" + message : "Message: (none)",
        ].filter(Boolean);

        var mailto =
          "mailto:" +
          to +
          "?subject=" +
          encodeURIComponent(subject) +
          "&body=" +
          encodeURIComponent(bodyParts.join("\n"));
        window.location.href = mailto;

        form.innerHTML =
          '<div class="enquiry-thanks"><h2>Thanks - we will be in touch shortly.</h2><p>Your mail app should have opened. If it did not, email <a href="mailto:' +
          to +
          '">' +
          to +
          "</a> with your name and mobile.</p></div>";
      });
    });
  }

  function setupListingGallery() {
    var gallery = document.querySelector(".js-gallery");
    if (!gallery) return;

    var dataNode = document.getElementById("listing-data");
    if (!dataNode) return;

    var data;
    try {
      data = JSON.parse(dataNode.textContent || "{}");
    } catch (error) {
      data = {};
    }
    if (!Array.isArray(data.gallery) || data.gallery.length < 1) return;

    var main = gallery.querySelector(".listing-main-image");
    var counter = gallery.querySelector(".gallery-counter");
    var thumbs = Array.from(gallery.querySelectorAll(".gallery-thumb"));
    var prev = gallery.querySelector(".gallery-prev");
    var next = gallery.querySelector(".gallery-next");
    var current = 0;

    function sync() {
      main.src = data.gallery[current];
      main.alt = data.title || "";
      counter.textContent = current + 1 + " of " + data.gallery.length;
      thumbs.forEach(function (thumb, idx) {
        thumb.classList.toggle("is-active", idx === current);
      });
    }

    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        var idx = Number(thumb.getAttribute("data-index"));
        if (!Number.isNaN(idx)) {
          current = idx;
          sync();
        }
      });
    });

    if (prev) {
      prev.addEventListener("click", function () {
        current = (current - 1 + data.gallery.length) % data.gallery.length;
        sync();
      });
    }

    if (next) {
      next.addEventListener("click", function () {
        current = (current + 1) % data.gallery.length;
        sync();
      });
    }

    sync();
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupInventoryBrowser();
    setupEnquiryForms();
    setupListingGallery();
  });
})();
