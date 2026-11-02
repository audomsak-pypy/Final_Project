// clientside: อ่าน prefers-color-scheme ส่งเข้า store "theme" และฟัง event เปลี่ยนโหมด
window.dash_clientside = Object.assign({}, window.dash_clientside, {
  adidur: {
    initTheme: function () {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      if (!window.__adidurThemeListener) {
        window.__adidurThemeListener = true;
        var handler = function (e) {
          window.dash_clientside.set_props("store-theme", { data: e.matches ? "dark" : "light" });
        };
        if (mq.addEventListener) mq.addEventListener("change", handler);
        else if (mq.addListener) mq.addListener(handler);
      }
      return mq.matches ? "dark" : "light";
    },
  },
});
