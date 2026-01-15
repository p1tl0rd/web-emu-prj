// Import Firebase SDK (Modular)
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
// Added 'push' and 'onValue' for profile management
import { getDatabase, ref, set, get, child, push, onValue } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyA2NxsUMKr6-A5Ql9_6GlXryoRZQlsgaE8",
    authDomain: "emujs-e36cc.firebaseapp.com",
    databaseURL: "https://emujs-e36cc-default-rtdb.firebaseio.com",
    projectId: "emujs-e36cc",
    storageBucket: "emujs-e36cc.firebasestorage.app",
    messagingSenderId: "237136618563",
    appId: "1:237136618563:web:da75d27b0485a8aadb60f6",
    measurementId: "G-C1QZBMPKJL"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// Export db and needed functions
// We removed auth exports since we are using a custom profile system
export { app, db, ref, set, get, child, push, onValue };
