'use strict';

/* eslint-enable max-len */

self.addEventListener('install', function (event) {
  console.log('Service Worker installing.');
});

self.addEventListener('activate', function (event) {
  console.log('Service Worker activating.');
});

self.addEventListener('push', function (event) {
  console.log('[Service Worker] Push Received.');
  const pushData = event.data.text();
  console.log(`[Service Worker] Push received this data - "${pushData}"`);
  let data, title, body, image;
  try {
    data = JSON.parse(pushData);
    title = data.title;
    body = data.body;
    image = data.image;
  } catch (e) {
    title = "Untitled";
    body = pushData;
  }
  const options = {
    body: body,
    image: image
  };
  console.log(title, options);

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});