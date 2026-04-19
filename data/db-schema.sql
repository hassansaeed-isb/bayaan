-- Create database
CREATE DATABASE IF NOT EXISTS bayaan
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE bayaan;

-- ----------------------------
-- Surahs
-- ----------------------------
CREATE TABLE surahs (
    id INT PRIMARY KEY,
    name_arabic VARCHAR(100),
    name_english VARCHAR(100)
);

-- ----------------------------
-- Ayahs
-- ----------------------------
CREATE TABLE ayahs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    surah_id INT,
    ayah_number INT,
    UNIQUE KEY unique_ayah (surah_id, ayah_number),
    FOREIGN KEY (surah_id) REFERENCES surahs(id)
);

-- ----------------------------
-- Ayah Words
-- ----------------------------
CREATE TABLE ayah_words (
    id BIGINT PRIMARY KEY,
    surah_id INT NOT NULL,
    ayah_number INT NOT NULL,
    word_index INT NOT NULL,
    location VARCHAR(20),
    text TEXT NOT NULL,
    is_symbol BOOLEAN DEFAULT FALSE,

    INDEX idx_ayah (surah_id, ayah_number),
    INDEX idx_word (surah_id, ayah_number, word_index),

    FOREIGN KEY (surah_id) REFERENCES surahs(id)
);

-- ----------------------------
-- Translations
-- ----------------------------
CREATE TABLE translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    language VARCHAR(10) NOT NULL,
    direction ENUM('rtl', 'ltr') NOT NULL
);

-- ----------------------------
-- Translation Segments
-- ----------------------------
CREATE TABLE translation_segments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    surah_id INT NOT NULL,
    ayah_number INT NOT NULL,
    translation_id INT NOT NULL,

    segment_index INT NOT NULL,

    word_start INT NOT NULL,
    word_end INT NOT NULL,

    translation_text TEXT NOT NULL,

    INDEX idx_lookup (translation_id, surah_id, ayah_number),
    INDEX idx_segment (surah_id, ayah_number, word_start, word_end),

    FOREIGN KEY (translation_id) REFERENCES translations(id),
    FOREIGN KEY (surah_id) REFERENCES surahs(id)
);

INSERT INTO surahs (id, name_arabic, name_english) VALUES
(1, 'الفاتحة', 'Al-Fatiha'),
(2, 'البقرة', 'Al-Baqarah'),
(3, 'آل عمران', 'Aal-E-Imran'),
(4, 'النساء', 'An-Nisa'),
(5, 'المائدة', 'Al-Ma\'idah'),
(6, 'الأنعام', 'Al-An\'am'),
(7, 'الأعراف', 'Al-A\'raf'),
(8, 'الأنفال', 'Al-Anfal'),
(9, 'التوبة', 'At-Tawbah'),
(10, 'يونس', 'Yunus'),
(11, 'هود', 'Hud'),
(12, 'يوسف', 'Yusuf'),
(13, 'الرعد', 'Ar-Ra\'d'),
(14, 'إبراهيم', 'Ibrahim'),
(15, 'الحجر', 'Al-Hijr'),
(16, 'النحل', 'An-Nahl'),
(17, 'الإسراء', 'Al-Isra'),
(18, 'الكهف', 'Al-Kahf'),
(19, 'مريم', 'Maryam'),
(20, 'طه', 'Ta-Ha'),
(21, 'الأنبياء', 'Al-Anbiya'),
(22, 'الحج', 'Al-Hajj'),
(23, 'المؤمنون', 'Al-Mu\'minun'),
(24, 'النور', 'An-Nur'),
(25, 'الفرقان', 'Al-Furqan'),
(26, 'الشعراء', 'Ash-Shu\'ara'),
(27, 'النمل', 'An-Naml'),
(28, 'القصص', 'Al-Qasas'),
(29, 'العنكبوت', 'Al-Ankabut'),
(30, 'الروم', 'Ar-Rum'),
(31, 'لقمان', 'Luqman'),
(32, 'السجدة', 'As-Sajdah'),
(33, 'الأحزاب', 'Al-Ahzab'),
(34, 'سبأ', 'Saba'),
(35, 'فاطر', 'Fatir'),
(36, 'يس', 'Ya-Sin'),
(37, 'الصافات', 'As-Saffat'),
(38, 'ص', 'Sad'),
(39, 'الزمر', 'Az-Zumar'),
(40, 'غافر', 'Ghafir'),
(41, 'فصلت', 'Fussilat'),
(42, 'الشورى', 'Ash-Shura'),
(43, 'الزخرف', 'Az-Zukhruf'),
(44, 'الدخان', 'Ad-Dukhan'),
(45, 'الجاثية', 'Al-Jathiyah'),
(46, 'الأحقاف', 'Al-Ahqaf'),
(47, 'محمد', 'Muhammad'),
(48, 'الفتح', 'Al-Fath'),
(49, 'الحجرات', 'Al-Hujurat'),
(50, 'ق', 'Qaf'),
(51, 'الذاريات', 'Adh-Dhariyat'),
(52, 'الطور', 'At-Tur'),
(53, 'النجم', 'An-Najm'),
(54, 'القمر', 'Al-Qamar'),
(55, 'الرحمن', 'Ar-Rahman'),
(56, 'الواقعة', 'Al-Waqi\'ah'),
(57, 'الحديد', 'Al-Hadid'),
(58, 'المجادلة', 'Al-Mujadila'),
(59, 'الحشر', 'Al-Hashr'),
(60, 'الممتحنة', 'Al-Mumtahanah'),
(61, 'الصف', 'As-Saff'),
(62, 'الجمعة', 'Al-Jumu\'ah'),
(63, 'المنافقون', 'Al-Munafiqun'),
(64, 'التغابن', 'At-Taghabun'),
(65, 'الطلاق', 'At-Talaq'),
(66, 'التحريم', 'At-Tahrim'),
(67, 'الملك', 'Al-Mulk'),
(68, 'القلم', 'Al-Qalam'),
(69, 'الحاقة', 'Al-Haqqah'),
(70, 'المعارج', 'Al-Ma\'arij'),
(71, 'نوح', 'Nuh'),
(72, 'الجن', 'Al-Jinn'),
(73, 'المزمل', 'Al-Muzzammil'),
(74, 'المدثر', 'Al-Muddathir'),
(75, 'القيامة', 'Al-Qiyamah'),
(76, 'الإنسان', 'Al-Insan'),
(77, 'المرسلات', 'Al-Mursalat'),
(78, 'النبأ', 'An-Naba'),
(79, 'النازعات', 'An-Nazi\'at'),
(80, 'عبس', 'Abasa'),
(81, 'التكوير', 'At-Takwir'),
(82, 'الانفطار', 'Al-Infitar'),
(83, 'المطففين', 'Al-Mutaffifin'),
(84, 'الانشقاق', 'Al-Inshiqaq'),
(85, 'البروج', 'Al-Buruj'),
(86, 'الطارق', 'At-Tariq'),
(87, 'الأعلى', 'Al-A\'la'),
(88, 'الغاشية', 'Al-Ghashiyah'),
(89, 'الفجر', 'Al-Fajr'),
(90, 'البلد', 'Al-Balad'),
(91, 'الشمس', 'Ash-Shams'),
(92, 'الليل', 'Al-Layl'),
(93, 'الضحى', 'Ad-Duha'),
(94, 'الشرح', 'Ash-Sharh'),
(95, 'التين', 'At-Tin'),
(96, 'العلق', 'Al-Alaq'),
(97, 'القدر', 'Al-Qadr'),
(98, 'البينة', 'Al-Bayyinah'),
(99, 'الزلزلة', 'Az-Zalzalah'),
(100, 'العاديات', 'Al-Adiyat'),
(101, 'القارعة', 'Al-Qari\'ah'),
(102, 'التكاثر', 'At-Takathur'),
(103, 'العصر', 'Al-Asr'),
(104, 'الهمزة', 'Al-Humazah'),
(105, 'الفيل', 'Al-Fil'),
(106, 'قريش', 'Quraysh'),
(107, 'الماعون', 'Al-Ma\'un'),
(108, 'الكوثر', 'Al-Kawthar'),
(109, 'الكافرون', 'Al-Kafirun'),
(110, 'النصر', 'An-Nasr'),
(111, 'المسد', 'Al-Masad'),
(112, 'الإخلاص', 'Al-Ikhlas'),
(113, 'الفلق', 'Al-Falaq'),
(114, 'الناس', 'An-Nas');

INSERT INTO translations (name, language, direction)
VALUES ('bayan-ul-quran', 'urdu', 'rtl');