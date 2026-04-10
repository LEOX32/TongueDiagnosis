export default {
  login: {
    title: "登录",
    email: "您的邮箱",
    password: "您的密码",
    signIn: "登录",
    register: "注册",
    noAccount: "没有账号？",
    alreadyHave: "已有账号？",
    passwordTooShort: "密码太短",
    passwordTooLong: "密码太长",
    validEmail: "请输入有效的邮箱地址",
    userNotFound: "用户不存在",
    wrongPassword: "密码错误"
  },
  register: {
    title: "注册",
    email: "您的邮箱",
    password: "设置密码",
    confirmPassword: "确认密码",
    signUp: "注册",
    passwordTooShort: "密码太短",
    passwordTooLong: "密码太长",
    validEmail: "请输入有效的邮箱地址",
    noSpecialChars: "请不要使用特殊字符",
    passwordsDoNotMatch: "密码不匹配"
  },
  home: {
    welcome: "欢迎使用 TongueKit",
    title: "AI 舌诊诊断",
    subtitle: "随时随地获得专业舌诊服务",
    startButton: "开始诊断",
    features: {
      accurate: "精准分析",
      fast: "快速结果",
      secure: "安全隐私",
      ai: "AI 咨询"
    },
    hero: {
      badge: "AI 驱动的中医诊断",
      title1: "智能",
      title2: "舌诊",
      title3: "革命",
      subtitle: "体验中医的未来，我们的尖端 AI 技术为您提供即时、准确的舌诊和个性化健康见解，由深度学习技术驱动。",
      featureTags: {
        ai: "AI 驱动",
        instant: "即时结果",
        tcm: "中医整合"
      }
    },
    cards: {
      aiAnalysis: {
        title: "AI 舌诊分析",
        description: "先进的深度学习算法以 95%+ 的准确率分析舌头特征，在几秒钟内提供全面的中医诊断。",
        stats: {
          accuracy: "准确率",
          time: "分析时间"
        }
      },
      healthTracking: {
        title: "健康跟踪",
        description: "通过详细报告、历史比较和个性化建议监控您的健康旅程。",
        features: {
          visual: "可视化报告",
          progress: "进度跟踪"
        }
      },
      expertConsult: {
        title: "专家咨询",
        description: "与认证的中医从业者联系，获取详细的咨询和治疗建议。",
        features: {
          experts: "认证专家",
          chat: "实时聊天"
        }
      }
    }
  },
  check: {
    title: "舌诊诊断",
    upload: "上传舌头图像",
    drag: "将您的舌头图像拖拽到此处",
    or: "或",
    select: "选择图像",
    analyze: "分析",
    result: "诊断结果",
    tongueColor: "舌头颜色",
    coatingColor: "舌苔颜色",
    tongueThickness: "舌头厚度",
    rotGreasy: "腻度",
    recordName: "输入记录名称",
    add: "添加",
    clear: "清空",
    clearConfirm: "确定要清空所有记录吗？此操作不可恢复！",
    clearSuccess: "记录清空成功",
    clearFailed: "记录清空失败，请重试",
    viewDetails: "查看记录详情",
    addNew: "添加",
    duplicateNameError: "记录名称已存在，请使用不同的名称。",
    deleteSuccess: "记录删除成功",
    deleteFailed: "记录删除失败，请重试"
  },
  health: {
    title: "健康跟踪",
    subtitle: "通过详细报告、历史比较和个性化建议监控您的健康旅程",
    visualReports: "可视化报告",
    progressTracking: "进度跟踪",
    generateReport: "生成报告",
    dailyReport: "日报",
    weeklyReport: "周报",
    monthlyReport: "月报",
    overallScore: "整体评分",
    tongueHealth: "舌象健康",
    trend: "趋势",
    improving: "改善中",
    stable: "稳定",
    declining: "下降",
    recommendations: "个性化建议",
    aiRecommendation: "AI 智能建议",
    diet: "饮食建议",
    lifestyle: "生活方式",
    exercise: "运动建议",
    sleep: "睡眠建议",
    noData: "暂无数据",
    noReport: "暂无报告",
    generateSuccess: "报告生成成功",
    totalAnalyses: "总分析次数",
    activeRecommendations: "进行中建议"
  },
  upload: {
    drag: "将文件拖拽到此处或",
    click: "点击此处上传照片"
  },
  chat: {
    welcome: "# 👋 欢迎使用 **AI 舌诊诊断**！\n\n📸 **请先上传您的舌头图像。**，AI 将基于中医理论进行智能分析并提供健康建议。\n\n🔍 **如何拍摄舌头照片？**\n1. 在自然光下拍摄，避免过暗或过亮。\n2. 放松舌头，尽可能向外伸展，不要用力。\n3. 保持清洁，避免食物残渣影响判断。\n\n💡 **免责声明**  \n本系统提供的分析结果仅供参考，不能替代专业医生的诊断。如果您有任何健康问题，请咨询中医医生或专业医疗专家。\n\n➡ **请上传您的舌头图像，让我们开始吧！**",
    thinking: "思考中...",
    playAudio: "播放音频",
    requestTimeout: "请求超时，请重试。",
    errorOccurred: "遇到错误，请重试。",
    generating: "生成中..."
  },
  result: {
    title: "诊断结果",
    noResults: "暂无检测结果。",
    tongueColor: "舌色",
    coatingColor: "舌苔颜色",
    tongueThickness: "舌头厚度",
    rotGreasy: "腻度",
    image: "图片",
    clickToView: "点击查看",
    diagnosisResult: "检测结果",
    wait: "请等待检测进行中。",
    noTongue: "未检测到舌头图像，请重新上传清晰的舌头图像。",
    multipleTongues: "检测到多张舌头图像，请重新拍摄并上传。",
    fileTypeError: "文件类型不正确，请检查并重新上传。",
    tongueColors: {
      0: "淡白舌",
      1: "淡红舌",
      2: "红舌",
      3: "绛舌",
      4: "青紫舌"
    },
    coatingColors: {
      0: "白苔",
      1: "黄苔",
      2: "灰黑苔"
    },
    rotGreasyTypes: {
      0: "舌苔腻",
      1: "舌苔腐"
    },
    tongueThickness: {
      0: "舌头薄",
      1: "舌头厚"
    }
  },
  nav: {
    home: "首页",
    examination: "舌诊",
    signIn: "登录",
    logout: "退出登录",
    profile: "个人资料"
  },
  user: {
    premium: "高级用户"
  },
  language: {
    english: "English",
    chinese: "中文",
    spanish: "Español",
    french: "Français",
    german: "Deutsch",
    japanese: "日本語",
    korean: "한국어"
  },
  guide: {
    welcome: "欢迎开始您的AI舌诊诊断之旅",
    clickLeft: "点击左侧",
    obtainAnalysis: "获取中医舌象分析",
    clickHere: "点击这里添加或查看对话"
  },
  app: {
    tongue: "舌诊",
    diagnosis: "诊断"
  },
  input: {
    placeholder: "请在此输入。"
  },
  help: "帮助",
  clear: "清空",
  export: "导出",
  reset: "重置",
  search: "搜索",
  searchPlaceholder: "搜索聊天记录...",
  noResults: "没有找到相关结果",
  user: "用户",
  ai: "AI"
}