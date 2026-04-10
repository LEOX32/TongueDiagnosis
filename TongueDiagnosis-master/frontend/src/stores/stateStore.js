import {defineStore} from 'pinia';
import settings from '../config/config.js';

export const useStateStore = defineStore('state', {
    state: () => ({
        isOpenValue: 0,
        userImagePath: "./static/userDefault.jpg",
        aiImagePath: "./static/aiDefault.jpg",
        audioType: 'D',
        baseUrl: settings.ServerUrl + "/model",
        chatHistory: [],
        infoHistory: [],
        isPlayed: false,
        gender: "male",
        personalPrompt: "",
        isShow: true,
        language: 'zh',
        token: localStorage.getItem('token') || '',
        isSidebarCollapsed: false,
        theme: localStorage.getItem('theme') || 'light',
        mainComponent: null
    }),
    actions: {
        initialize() {
            // 确保使用正确的服务器URL
            this.baseUrl = settings.ServerUrl + "/model";
        },
        setIsOpenValue(newValue) {
            this.isOpenValue = newValue;
        },
        setuserImagePath(newValue) {
            this.userImagePath = newValue;
        },
        setaiImagePath(newValue) {
            this.aiImagePath = newValue;
        },
        setaudioType(newValue) {
            this.audioType = newValue;
        },
        setbaseUrl(newValue) {
            this.baseUrl = newValue;
        },
        setisPlayed(newValue) {
            this.isPlayed = newValue;
        },
        setGender(newValue) {
            this.gender = newValue;
        },
        setPersonalPrompt(newValue) {
            this.personalPrompt = newValue;
        },
        setIsShow(newValue) {
            this.isShow = newValue;
        },
        setChatHistory(newValue) {
            this.chatHistory = newValue;
        },
        setInfoHistory(newValue) {
            this.infoHistory = newValue;
        },
        setLanguage(newValue) {
            this.language = newValue;
        },
        setToken(newValue) {
            this.token = newValue;
        },
        toggleSidebar() {
            this.isSidebarCollapsed = !this.isSidebarCollapsed;
        },
        setSidebarCollapsed(newValue) {
            this.isSidebarCollapsed = newValue;
        },
        setTheme(newValue) {
            this.theme = newValue;
            localStorage.setItem('theme', newValue);
            document.documentElement.setAttribute('data-theme', newValue);
        },
        toggleTheme() {
            this.theme = this.theme === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', this.theme);
            document.documentElement.setAttribute('data-theme', this.theme);
        },
        setMainComponent(newValue) {
            this.mainComponent = newValue;
        },
        getAllSessions() {
            if (this.mainComponent && this.mainComponent.getAllSessions) {
                return this.mainComponent.getAllSessions();
            }
            return [];
        },
        scrollToMessage(sessionId, messageIndex) {
            if (this.mainComponent && this.mainComponent.scrollToMessage) {
                this.mainComponent.scrollToMessage(sessionId, messageIndex);
            }
        }
    },
});

export const useStore = useStateStore;
