/*!
 * coi-serviceworker v0.1.7 - Milton Candelero
 * https://github.com/gzuidhof/coi-serviceworker
 * Released under the MIT license.
 */

if ("serviceWorker" in navigator) {
    if (navigator.serviceWorker.controller) {
        console.log("coi-serviceworker active");
    } else {
        navigator.serviceWorker.register("coi-serviceworker.js").then(
            (registration) => {
                console.log("coi-serviceworker registered");
                window.location.reload();
            },
            (err) => {
                console.log("coi-serviceworker registration failed: ", err);
            }
        );
    }
}

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", function (event) {
    if (event.request.cache === "only-if-cached" && event.request.mode !== "same-origin") {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                if (response.status === 0) {
                    return response;
                }

                const newHeaders = new Headers(response.headers);
                newHeaders.set("Cross-Origin-Embedder-Policy", "require-corp");
                newHeaders.set("Cross-Origin-Opener-Policy", "same-origin");

                return new Response(response.body, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: newHeaders,
                });
            })
            .catch((e) => console.error(e))
    );
});
