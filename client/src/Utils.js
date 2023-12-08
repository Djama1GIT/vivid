export function changeURLParam(key, value) {
   // Получаем текущий URL
   let currentURL = new URL(window.location.href);

   // Изменяем параметр
   currentURL.searchParams.set(key, value);

   // Устанавливаем новый URL
   window.history.pushState({}, '', currentURL);
}
