// ========================================
// ADVANCED WIKIPEDIA BOT ACTIVITY
// Features: Local Image Caching (Offline Support), Dynamic RTL/LTR,
// Live Search (Autocomplete), Multi-Language (FA/DA/PS/AR/EN),
// Copy, Share, Open in Browser, Cancel/Stop Animation, Rename & History Search.
// ========================================

final String PREFS_NAME = "WikiSingleActivityPrefs";

final String[] activeChatId = new String[]{
    String.valueOf(System.currentTimeMillis())
};

final boolean[] isAnimating = new boolean[]{false};
final boolean[] cancelRequested = new boolean[]{false};

// ========================================
// MAIN VIEWS
// ========================================

final android.widget.FrameLayout mainContainer =
    new android.widget.FrameLayout(ChatbotActivity.this);

final android.widget.LinearLayout listPage =
    new android.widget.LinearLayout(ChatbotActivity.this);

final android.widget.LinearLayout chatPage =
    new android.widget.LinearLayout(ChatbotActivity.this);

final android.widget.LinearLayout itemsContainer =
    new android.widget.LinearLayout(ChatbotActivity.this);

final android.widget.LinearLayout messagesBox =
    new android.widget.LinearLayout(ChatbotActivity.this);

final android.widget.ScrollView chatScroll =
    new android.widget.ScrollView(ChatbotActivity.this);

// Suggestions Layout for Live Search
final android.widget.LinearLayout suggestionsContainer =
    new android.widget.LinearLayout(ChatbotActivity.this);

mainContainer.setBackgroundColor(0xFF121212);


// ========================================
// VIEW 1: CHAT HISTORY PAGE
// ========================================

listPage.setOrientation(android.widget.LinearLayout.VERTICAL);
listPage.setPadding(24, 24, 24, 24);

android.widget.LinearLayout listTopBar =
    new android.widget.LinearLayout(ChatbotActivity.this);
listTopBar.setOrientation(android.widget.LinearLayout.HORIZONTAL);
listTopBar.setGravity(android.view.Gravity.CENTER_VERTICAL);

android.widget.TextView listTitle =
    new android.widget.TextView(ChatbotActivity.this);
listTitle.setText("تاریخچه چت‌ها / History");
listTitle.setTextSize(20);
listTitle.setTypeface(null, android.graphics.Typeface.BOLD);
listTitle.setTextColor(0xFFFFFFFF);

android.widget.LinearLayout.LayoutParams listTitleParams =
    new android.widget.LinearLayout.LayoutParams(0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f);
listTitle.setLayoutParams(listTitleParams);

listTopBar.addView(listTitle);
listPage.addView(listTopBar);

// Search Bar for History
final android.widget.EditText searchHistoryField =
    new android.widget.EditText(ChatbotActivity.this);
searchHistoryField.setHint("جستجو در چت‌ها / Search History...");
searchHistoryField.setHintTextColor(0xFF888888);
searchHistoryField.setTextColor(0xFFFFFFFF);
searchHistoryField.setTextSize(14);
searchHistoryField.setPadding(20, 16, 20, 16);
android.graphics.drawable.GradientDrawable searchBg = new android.graphics.drawable.GradientDrawable();
searchBg.setColor(0xFF1E1E1E);
searchBg.setCornerRadius(16f);
searchHistoryField.setBackground(searchBg);

android.widget.LinearLayout.LayoutParams searchHistoryParams =
    new android.widget.LinearLayout.LayoutParams(android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT);
searchHistoryParams.setMargins(0, 16, 0, 16);
searchHistoryField.setLayoutParams(searchHistoryParams);
listPage.addView(searchHistoryField);

// New Chat Button
android.widget.Button startNewBtn =
    new android.widget.Button(ChatbotActivity.this);
startNewBtn.setText("+ شروع چت جدید / NEW CHAT");
startNewBtn.setTextSize(16);
startNewBtn.setTextColor(0xFFFFFFFF);
startNewBtn.setTypeface(null, android.graphics.Typeface.BOLD);
android.graphics.drawable.GradientDrawable newBtnBg = new android.graphics.drawable.GradientDrawable();
newBtnBg.setColor(0xFF0D6EFD);
newBtnBg.setCornerRadius(20f);
startNewBtn.setBackground(newBtnBg);

android.widget.LinearLayout.LayoutParams startNewParams =
    new android.widget.LinearLayout.LayoutParams(android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT);
startNewParams.setMargins(0, 0, 0, 20);
startNewBtn.setLayoutParams(startNewParams);
listPage.addView(startNewBtn);

// History Scroll Area
android.widget.ScrollView listScroll =
    new android.widget.ScrollView(ChatbotActivity.this);
itemsContainer.setOrientation(android.widget.LinearLayout.VERTICAL);

listScroll.addView(itemsContainer, new android.widget.ScrollView.LayoutParams(
    android.widget.ScrollView.LayoutParams.MATCH_PARENT,
    android.widget.ScrollView.LayoutParams.WRAP_CONTENT));

listPage.addView(listScroll, new android.widget.LinearLayout.LayoutParams(
    android.widget.LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f));


// ========================================
// VIEW 2: CHAT PAGE
// ========================================

chatPage.setOrientation(android.widget.LinearLayout.VERTICAL);
chatPage.setPadding(16, 16, 16, 16);
chatPage.setVisibility(android.view.View.GONE);

// Chat Top Bar
android.widget.LinearLayout chatTopBar =
    new android.widget.LinearLayout(ChatbotActivity.this);
chatTopBar.setOrientation(android.widget.LinearLayout.HORIZONTAL);
chatTopBar.setGravity(android.view.Gravity.CENTER_VERTICAL);

// Back Button
android.widget.ImageView backBtn =
    new android.widget.ImageView(ChatbotActivity.this);
backBtn.setImageResource(android.R.drawable.ic_menu_revert);
backBtn.setColorFilter(0xFFFFFFFF);
backBtn.setPadding(16, 16, 16, 16);
backBtn.setFocusable(true);
backBtn.setClickable(true);
android.graphics.drawable.GradientDrawable backBg = new android.graphics.drawable.GradientDrawable();
backBg.setColor(0xFF2C2C2C);
backBg.setCornerRadius(100f);
backBtn.setBackground(backBg);
backBtn.setLayoutParams(new android.widget.LinearLayout.LayoutParams(96, 96));

android.widget.TextView chatTitle =
    new android.widget.TextView(ChatbotActivity.this);
chatTitle.setText("ویکی‌پدیا Bot");
chatTitle.setTextSize(18);
chatTitle.setTypeface(null, android.graphics.Typeface.BOLD);
chatTitle.setTextColor(0xFFFFFFFF);
chatTitle.setPadding(20, 0, 0, 0);

chatTopBar.addView(backBtn);
chatTopBar.addView(chatTitle);
chatPage.addView(chatTopBar);

// Chat Scroll
chatScroll.setLayoutParams(new android.widget.LinearLayout.LayoutParams(
    android.widget.LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f));
messagesBox.setOrientation(android.widget.LinearLayout.VERTICAL);
messagesBox.setPadding(8, 8, 8, 8);
chatScroll.addView(messagesBox, new android.widget.ScrollView.LayoutParams(
    android.widget.ScrollView.LayoutParams.MATCH_PARENT, android.widget.ScrollView.LayoutParams.WRAP_CONTENT));
chatPage.addView(chatScroll);

// Live Search Suggestions Layout
suggestionsContainer.setOrientation(android.widget.LinearLayout.VERTICAL);
suggestionsContainer.setVisibility(android.view.View.GONE);
android.graphics.drawable.GradientDrawable sugBg = new android.graphics.drawable.GradientDrawable();
sugBg.setColor(0xFF222222);
sugBg.setCornerRadius(16f);
suggestionsContainer.setBackground(sugBg);
chatPage.addView(suggestionsContainer);

// Bottom Bar Layout
android.widget.LinearLayout bottomBar =
    new android.widget.LinearLayout(ChatbotActivity.this);
bottomBar.setOrientation(android.widget.LinearLayout.HORIZONTAL);
bottomBar.setGravity(android.view.Gravity.CENTER_VERTICAL);
bottomBar.setPadding(0, 16, 0, 8);

final android.widget.EditText inputField =
    new android.widget.EditText(ChatbotActivity.this);
inputField.setHint("موضوع به فارسی، دری، پشتو، عربی یا انگلیسی...");
inputField.setHintTextColor(0xFF888888);
inputField.setTextColor(0xFFFFFFFF);
inputField.setTextSize(15);
inputField.setMinLines(1);
inputField.setMaxLines(4);
inputField.setPadding(24, 20, 24, 20);

android.graphics.drawable.GradientDrawable inputBG = new android.graphics.drawable.GradientDrawable();
inputBG.setColor(0xFF1E1E1E);
inputBG.setCornerRadius(24f);
inputBG.setStroke(2, 0xFF333333);
inputField.setBackground(inputBG);

android.widget.LinearLayout.LayoutParams inputParams =
    new android.widget.LinearLayout.LayoutParams(0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f);
inputParams.setMargins(0, 0, 12, 0);
inputField.setLayoutParams(inputParams);

final android.widget.ImageView sendBtn =
    new android.widget.ImageView(ChatbotActivity.this);
sendBtn.setImageResource(android.R.drawable.ic_menu_send);
sendBtn.setColorFilter(0xFFFFFFFF);
sendBtn.setPadding(20, 20, 20, 20);
sendBtn.setFocusable(true);
sendBtn.setClickable(true);

android.graphics.drawable.GradientDrawable sendBg = new android.graphics.drawable.GradientDrawable();
sendBg.setColor(0xFF0D6EFD);
sendBg.setCornerRadius(100f);
sendBtn.setBackground(sendBg);

android.widget.LinearLayout.LayoutParams sendParams =
    new android.widget.LinearLayout.LayoutParams(110, 110);
sendParams.gravity = android.view.Gravity.CENTER_VERTICAL;
sendBtn.setLayoutParams(sendParams);

bottomBar.addView(inputField);
bottomBar.addView(sendBtn);
chatPage.addView(bottomBar);

mainContainer.addView(listPage);
mainContainer.addView(chatPage);
setContentView(mainContainer);


// ========================================
// UI CONTROLLER
// ========================================

class UIController {

    boolean isRTL(String text) {
        if (text == null) return false;
        for (char c : text.toCharArray()) {
            Character.UnicodeBlock block = Character.UnicodeBlock.of(c);
            if (block == Character.UnicodeBlock.ARABIC || 
                block == Character.UnicodeBlock.ARABIC_SUPPLEMENT ||
                block == Character.UnicodeBlock.ARABIC_EXTENDED_A) {
                return true;
            }
        }
        return false;
    }

    String getDomain(String text) {
        if (isRTL(text)) {
            return "fa.wikipedia.org";
        }
        return "en.wikipedia.org";
    }

    // Download and Cache Image to Local Storage for Offline Use
    void loadAndCacheImage(final String imageUrl, final android.widget.ImageView imageView, final Runnable onSaved) {
        if (imageUrl == null || imageUrl.isEmpty()) return;

        // Generate unique local filename from URL hash
        final String fileName = "wiki_img_" + Math.abs(imageUrl.hashCode()) + ".jpg";
        final java.io.File file = new java.io.File(getFilesDir(), fileName);

        if (file.exists()) {
            android.graphics.Bitmap bitmap = android.graphics.BitmapFactory.decodeFile(file.getAbsolutePath());
            if (bitmap != null) {
                imageView.setImageBitmap(bitmap);
                imageView.setVisibility(android.view.View.VISIBLE);
                if (onSaved != null) onSaved.run();
                return;
            }
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    java.net.URL url = new java.net.URL(imageUrl);
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                    conn.setDoInput(true);
                    conn.connect();
                    java.io.InputStream input = conn.getInputStream();
                    final android.graphics.Bitmap bitmap = android.graphics.BitmapFactory.decodeStream(input);

                    // Save bitmap to internal storage
                    java.io.FileOutputStream fos = new java.io.FileOutputStream(file);
                    bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 90, fos);
                    fos.flush();
                    fos.close();

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            imageView.setImageBitmap(bitmap);
                            imageView.setVisibility(android.view.View.VISIBLE);
                            if (onSaved != null) onSaved.run();
                        }
                    });
                } catch (Exception e) {
                    // Try showing if already partly saved
                    if (file.exists()) {
                        final android.graphics.Bitmap bitmap = android.graphics.BitmapFactory.decodeFile(file.getAbsolutePath());
                        if (bitmap != null) {
                            runOnUiThread(new Runnable() {
                                @Override
                                public void run() {
                                    imageView.setImageBitmap(bitmap);
                                    imageView.setVisibility(android.view.View.VISIBLE);
                                }
                            });
                        }
                    }
                }
            }
        }).start();
    }

    android.graphics.drawable.Drawable createCopyIcon() {
        android.graphics.Bitmap bitmap = android.graphics.Bitmap.createBitmap(64, 64, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas canvas = new android.graphics.Canvas(bitmap);
        android.graphics.Paint paint = new android.graphics.Paint();
        paint.setColor(0xFFFFFFFF);
        paint.setStyle(android.graphics.Paint.Style.STROKE);
        paint.setStrokeWidth(5f);
        paint.setAntiAlias(true);
        canvas.drawRoundRect(new android.graphics.RectF(22, 10, 52, 42), 6, 6, paint);
        canvas.drawRoundRect(new android.graphics.RectF(12, 20, 42, 52), 6, 6, paint);
        return new android.graphics.drawable.BitmapDrawable(getResources(), bitmap);
    }

    void setSendButtonState(boolean isCancel) {
        if (isCancel) {
            sendBtn.setImageResource(android.R.drawable.ic_menu_close_clear_cancel);
            android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
            bg.setColor(0xFFD32F2F);
            bg.setCornerRadius(100f);
            sendBtn.setBackground(bg);
        } else {
            sendBtn.setImageResource(android.R.drawable.ic_menu_send);
            android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
            bg.setColor(0xFF0D6EFD);
            bg.setCornerRadius(100f);
            sendBtn.setBackground(bg);
        }
    }

    void addBubble(
        final String text,
        final String imageUrl,
        final String pageTitle,
        final boolean isUser,
        final boolean save,
        boolean animate
    ) {
        final android.widget.LinearLayout bubbleContainer = new android.widget.LinearLayout(ChatbotActivity.this);
        bubbleContainer.setOrientation(android.widget.LinearLayout.VERTICAL);

        boolean rtl = isRTL(text);

        android.widget.LinearLayout.LayoutParams params =
            new android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
            );
        params.setMargins(isUser ? 60 : 0, 10, isUser ? 0 : 60, 10);

        if (isUser) {
            android.graphics.drawable.GradientDrawable bubble = new android.graphics.drawable.GradientDrawable();
            bubble.setCornerRadius(24f);
            bubble.setColor(0xFF424242);
            bubbleContainer.setBackground(bubble);
        }

        bubbleContainer.setLayoutParams(params);

        if (isUser) {
            android.widget.TextView userTv = new android.widget.TextView(ChatbotActivity.this);
            userTv.setText(text);
            userTv.setTextSize(15);
            userTv.setTextColor(0xFFFFFFFF);
            userTv.setTextIsSelectable(true);
            userTv.setPadding(28, 20, 28, 20);
            if (rtl) userTv.setGravity(android.view.Gravity.RIGHT);
            bubbleContainer.addView(userTv);
        } else {
            // Optional Image View with Local Cache
            if (imageUrl != null && !imageUrl.isEmpty()) {
                final android.widget.ImageView imgView = new android.widget.ImageView(ChatbotActivity.this);
                imgView.setVisibility(android.view.View.GONE);
                imgView.setAdjustViewBounds(true);
                imgView.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
                imgView.setPadding(28, 20, 28, 0);
                bubbleContainer.addView(imgView);

                loadAndCacheImage(imageUrl, imgView, new Runnable() {
                    @Override
                    public void run() {
                        if (save) {
                            saveMessageToPrefs(text, imageUrl, pageTitle, isUser);
                        }
                    }
                });
            }

            final android.widget.LinearLayout textContainer = new android.widget.LinearLayout(ChatbotActivity.this);
            textContainer.setOrientation(android.widget.LinearLayout.VERTICAL);
            textContainer.setPadding(28, 16, 28, 10);
            bubbleContainer.addView(textContainer);

            if (animate) {
                isAnimating[0] = true;
                cancelRequested[0] = false;
                setSendButtonState(true);

                final String[] lines = text.split("\n", -1);
                final android.os.Handler handler = new android.os.Handler(android.os.Looper.getMainLooper());
                final int[] lineIndex = new int[]{0};

                Runnable lineAnimation = new Runnable() {
                    @Override
                    public void run() {
                        if (cancelRequested[0] || lineIndex[0] >= lines.length) {
                            isAnimating[0] = false;
                            setSendButtonState(false);
                            return;
                        }

                        final android.widget.TextView lineTv = new android.widget.TextView(ChatbotActivity.this);
                        String currentLine = lines[lineIndex[0]];
                        if (currentLine.trim().isEmpty()) {
                            lineTv.setText(" ");
                            lineTv.setHeight(20);
                        } else {
                            lineTv.setText(currentLine);
                        }

                        lineTv.setTextSize(15);
                        lineTv.setTextColor(0xFFE0E0E0);
                        lineTv.setTextIsSelectable(true);
                        if (isRTL(currentLine)) {
                            lineTv.setGravity(android.view.Gravity.RIGHT);
                        }

                        textContainer.addView(lineTv);
                        lineTv.setAlpha(0f);
                        lineTv.setTranslationY(-35f);
                        lineTv.animate().alpha(1f).translationY(0f).setDuration(200).start();

                        chatScroll.post(new Runnable() {
                            @Override
                            public void run() {
                                chatScroll.fullScroll(android.view.View.FOCUS_DOWN);
                            }
                        });

                        lineIndex[0]++;
                        handler.postDelayed(this, 220);
                    }
                };
                handler.post(lineAnimation);
            } else {
                String[] lines = text.split("\n", -1);
                for (String line : lines) {
                    android.widget.TextView lineTv = new android.widget.TextView(ChatbotActivity.this);
                    if (line.trim().isEmpty()) {
                        lineTv.setText(" ");
                        lineTv.setHeight(20);
                    } else {
                        lineTv.setText(line);
                    }
                    lineTv.setTextSize(15);
                    lineTv.setTextColor(0xFFE0E0E0);
                    lineTv.setTextIsSelectable(true);
                    if (isRTL(line)) lineTv.setGravity(android.view.Gravity.RIGHT);
                    textContainer.addView(lineTv);
                }
            }

            // Copy + Share + Open Browser
            android.widget.LinearLayout actionLayout = new android.widget.LinearLayout(ChatbotActivity.this);
            actionLayout.setOrientation(android.widget.LinearLayout.HORIZONTAL);
            actionLayout.setGravity(android.view.Gravity.END);
            actionLayout.setPadding(0, 4, 16, 12);

            if (pageTitle != null && !pageTitle.isEmpty()) {
                final android.widget.ImageView webBtn = new android.widget.ImageView(ChatbotActivity.this);
                webBtn.setImageResource(android.R.drawable.ic_menu_compass);
                webBtn.setColorFilter(0xFFFFFFFF);
                webBtn.setPadding(12, 12, 12, 12);
                webBtn.setFocusable(true);
                webBtn.setClickable(true);
                android.graphics.drawable.GradientDrawable webBg = new android.graphics.drawable.GradientDrawable();
                webBg.setColor(0xFF333333);
                webBg.setCornerRadius(50f);
                webBtn.setBackground(webBg);
                android.widget.LinearLayout.LayoutParams webParams = new android.widget.LinearLayout.LayoutParams(84, 84);
                webParams.setMargins(0, 0, 10, 0);
                webBtn.setLayoutParams(webParams);

                webBtn.setOnClickListener(new android.view.View.OnClickListener() {
                    @Override
                    public void onClick(android.view.View v) {
                        try {
                            String domain = getDomain(text);
                            String webUrl = "https://" + domain + "/wiki/" + java.net.URLEncoder.encode(pageTitle, "UTF-8");
                            android.content.Intent browserIntent = new android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(webUrl));
                            startActivity(browserIntent);
                        } catch (Exception e) {}
                    }
                });
                actionLayout.addView(webBtn);
            }

            final android.widget.ImageView copyBtn = new android.widget.ImageView(ChatbotActivity.this);
            copyBtn.setImageDrawable(createCopyIcon());
            copyBtn.setPadding(12, 12, 12, 12);
            copyBtn.setFocusable(true);
            copyBtn.setClickable(true);
            android.graphics.drawable.GradientDrawable copyBg = new android.graphics.drawable.GradientDrawable();
            copyBg.setColor(0xFF333333);
            copyBg.setCornerRadius(50f);
            copyBtn.setBackground(copyBg);
            android.widget.LinearLayout.LayoutParams copyParams = new android.widget.LinearLayout.LayoutParams(84, 84);
            copyParams.setMargins(0, 0, 10, 0);
            copyBtn.setLayoutParams(copyParams);

            copyBtn.setOnClickListener(new android.view.View.OnClickListener() {
                @Override
                public void onClick(android.view.View v) {
                    android.content.ClipboardManager clipboard = (android.content.ClipboardManager) getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                    android.content.ClipData clip = android.content.ClipData.newPlainText("Copied Text", text);
                    if (clipboard != null) {
                        clipboard.setPrimaryClip(clip);
                        android.widget.Toast.makeText(ChatbotActivity.this, "Copied ✓ کاپی شد", android.widget.Toast.LENGTH_SHORT).show();
                    }
                }
            });

            final android.widget.ImageView shareBtn = new android.widget.ImageView(ChatbotActivity.this);
            shareBtn.setImageResource(android.R.drawable.ic_menu_share);
            shareBtn.setColorFilter(0xFFFFFFFF);
            shareBtn.setPadding(12, 12, 12, 12);
            shareBtn.setFocusable(true);
            shareBtn.setClickable(true);
            android.graphics.drawable.GradientDrawable shareBg = new android.graphics.drawable.GradientDrawable();
            shareBg.setColor(0xFF333333);
            shareBg.setCornerRadius(50f);
            shareBtn.setBackground(shareBg);
            shareBtn.setLayoutParams(new android.widget.LinearLayout.LayoutParams(84, 84));

            shareBtn.setOnClickListener(new android.view.View.OnClickListener() {
                @Override
                public void onClick(android.view.View v) {
                    try {
                        android.content.Intent shareIntent = new android.content.Intent(android.content.Intent.ACTION_SEND);
                        shareIntent.setType("text/plain");
                        shareIntent.putExtra(android.content.Intent.EXTRA_TEXT, text);
                        startActivity(android.content.Intent.createChooser(shareIntent, "اشتراک‌گذاری / Share"));
                    } catch (Exception e) {}
                }
            });

            actionLayout.addView(copyBtn);
            actionLayout.addView(shareBtn);
            bubbleContainer.addView(actionLayout);
        }

        messagesBox.addView(bubbleContainer);

        if (animate) {
            bubbleContainer.setAlpha(0f);
            bubbleContainer.setTranslationY(40f);
            bubbleContainer.animate().alpha(1f).translationY(0f).setDuration(250).start();
        }

        chatScroll.post(new Runnable() {
            @Override
            public void run() {
                chatScroll.fullScroll(android.view.View.FOCUS_DOWN);
            }
        });

        if (save && (imageUrl == null || imageUrl.isEmpty())) {
            saveMessageToPrefs(text, imageUrl, pageTitle, isUser);
        }
    }

    void saveMessageToPrefs(String text, String imageUrl, String pageTitle, boolean isUser) {
        android.content.SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String history = prefs.getString(activeChatId[0], "");
        history += (isUser ? "[USER]" : "[BOT]") + text + (imageUrl != null ? "[IMG]" + imageUrl : "") + (pageTitle != null ? "[TITLE]" + pageTitle : "") + "[END_MSG]";
        prefs.edit().putString(activeChatId[0], history).apply();
    }

    void renderHistoryList(String filter) {
        itemsContainer.removeAllViews();
        android.content.SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        java.util.Map<String, ?> allEntries = prefs.getAll();

        if (allEntries.isEmpty()) {
            android.widget.TextView emptyTv = new android.widget.TextView(ChatbotActivity.this);
            emptyTv.setText("چت ذخیره‌شده‌ای وجود ندارد / No saved chats");
            emptyTv.setTextColor(0xFF888888);
            emptyTv.setTextSize(15);
            emptyTv.setPadding(0, 40, 0, 0);
            emptyTv.setGravity(android.view.Gravity.CENTER);
            itemsContainer.addView(emptyTv);
            return;
        }

        for (final java.util.Map.Entry<String, ?> entry : allEntries.entrySet()) {
            final String chatId = entry.getKey();
            if (!chatId.matches("\\d+")) continue;

            String chatData = String.valueOf(entry.getValue());
            String titleStr = "گفتگو " + chatId;

            if (chatData.contains("[USER]")) {
                int start = chatData.indexOf("[USER]") + 6;
                int end = chatData.indexOf("[END_MSG]", start);
                if (end > start) {
                    titleStr = chatData.substring(start, end)
                        .replace("شما:\n", "")
                        .replace("You:\n", "");

                    int imgIdx = titleStr.indexOf("[IMG]");
                    if (imgIdx != -1) {
                        titleStr = titleStr.substring(0, imgIdx);
                    }
                    if (titleStr.length() > 40) {
                        titleStr = titleStr.substring(0, 40) + "...";
                    }
                }
            }

            if (filter != null && !filter.isEmpty() && !titleStr.toLowerCase().contains(filter.toLowerCase())) {
                continue;
            }

            android.widget.LinearLayout historyItem = new android.widget.LinearLayout(ChatbotActivity.this);
            historyItem.setOrientation(android.widget.LinearLayout.HORIZONTAL);
            historyItem.setGravity(android.view.Gravity.CENTER_VERTICAL);

            android.graphics.drawable.GradientDrawable itemBG = new android.graphics.drawable.GradientDrawable();
            itemBG.setColor(0xFF1E1E1E);
            itemBG.setCornerRadius(16f);
            historyItem.setBackground(itemBG);

            android.widget.LinearLayout.LayoutParams historyParams = new android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT);
            historyParams.setMargins(0, 10, 0, 10);
            historyItem.setLayoutParams(historyParams);

            android.widget.TextView item = new android.widget.TextView(ChatbotActivity.this);
            item.setText(titleStr);
            item.setTextSize(15);
            item.setTextColor(0xFFFFFFFF);
            item.setPadding(30, 30, 20, 30);
            item.setLayoutParams(new android.widget.LinearLayout.LayoutParams(0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f));

            // Delete Single Item
            final android.widget.ImageView deleteBtn = new android.widget.ImageView(ChatbotActivity.this);
            deleteBtn.setImageResource(android.R.drawable.ic_menu_delete);
            deleteBtn.setColorFilter(0xFFFF5252);
            deleteBtn.setPadding(18, 18, 18, 18);
            deleteBtn.setFocusable(true);
            deleteBtn.setClickable(true);

            android.graphics.drawable.GradientDrawable deleteBg = new android.graphics.drawable.GradientDrawable();
            deleteBg.setColor(0xFF2C2C2C);
            deleteBg.setCornerRadius(100f);
            deleteBtn.setBackground(deleteBg);
            deleteBtn.setLayoutParams(new android.widget.LinearLayout.LayoutParams(80, 80));

            deleteBtn.setOnClickListener(new android.view.View.OnClickListener() {
                @Override
                public void onClick(android.view.View v) {
                    getSharedPreferences(PREFS_NAME, MODE_PRIVATE).edit().remove(chatId).apply();
                    renderHistoryList(searchHistoryField.getText().toString());
                }
            });

            item.setOnClickListener(new android.view.View.OnClickListener() {
                @Override
                public void onClick(android.view.View v) {
                    openChat(chatId);
                }
            });

            historyItem.addView(item);
            historyItem.addView(deleteBtn);
            itemsContainer.addView(historyItem);
        }
    }

    void openChat(String chatId) {
        activeChatId[0] = chatId;
        messagesBox.removeAllViews();
        android.content.SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String history = prefs.getString(chatId, "");

        if (!history.isEmpty()) {
            String[] msgs = history.split("\\[END_MSG\\]");
            for (String msg : msgs) {
                if (msg.startsWith("[USER]")) {
                    addBubble(msg.replaceFirst("\\[USER\\]", ""), null, null, true, false, false);
                } else if (msg.startsWith("[BOT]")) {
                    String raw = msg.replaceFirst("\\[BOT\\]", "");
                    String imgUrl = null;
                    String pTitle = null;

                    if (raw.contains("[IMG]")) {
                        int imgStart = raw.indexOf("[IMG]");
                        int titleStart = raw.indexOf("[TITLE]");
                        if (titleStart > imgStart && imgStart != -1) {
                            imgUrl = raw.substring(imgStart + 5, titleStart);
                            pTitle = raw.substring(titleStart + 7);
                        } else if (imgStart != -1) {
                            imgUrl = raw.substring(imgStart + 5);
                        }
                        if (imgStart != -1) {
                            raw = raw.substring(0, imgStart);
                        }
                    }
                    addBubble(raw, imgUrl, pTitle, false, false, false);
                }
            }
        } else {
            addBubble("HZR Wikipedia Bot:\n\nسلام! موضوع مورد نظرتان را به فارسی، دری، پشتو، عربی یا انگلیسی بنویسید.", null, null, false, false, true);
        }

        listPage.setVisibility(android.view.View.GONE);
        chatPage.setVisibility(android.view.View.VISIBLE);
    }

    void fetchSuggestions(final String query) {
        if (query.trim().length() < 2) {
            suggestionsContainer.setVisibility(android.view.View.GONE);
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    String domain = getDomain(query);
                    String encoded = java.net.URLEncoder.encode(query, "UTF-8");
                    String urlStr = "https://" + domain + "/w/api.php?action=opensearch&format=json&limit=4&search=" + encoded;

                    java.net.URL url = new java.net.URL(urlStr);
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                    conn.setRequestProperty("User-Agent", "Mozilla/5.0");

                    java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String l;
                    while ((l = reader.readLine()) != null) sb.append(l);
                    reader.close();

                    org.json.JSONArray arr = new org.json.JSONArray(sb.toString());
                    final org.json.JSONArray suggestions = arr.getJSONArray(1);

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            suggestionsContainer.removeAllViews();
                            if (suggestions.length() == 0) {
                                suggestionsContainer.setVisibility(android.view.View.GONE);
                                return;
                            }

                            for (int i = 0; i < suggestions.length(); i++) {
                                final String sug = suggestions.optString(i, "");
                                android.widget.TextView tv = new android.widget.TextView(ChatbotActivity.this);
                                tv.setText("🔍 " + sug);
                                tv.setTextColor(0xFFE0E0E0);
                                tv.setTextSize(14);
                                tv.setPadding(24, 16, 24, 16);
                                tv.setOnClickListener(new android.view.View.OnClickListener() {
                                    @Override
                                    public void onClick(android.view.View v) {
                                        inputField.setText(sug);
                                        suggestionsContainer.setVisibility(android.view.View.GONE);
                                        sendBtn.performClick();
                                    }
                                });
                                suggestionsContainer.addView(tv);
                            }
                            suggestionsContainer.setVisibility(android.view.View.VISIBLE);
                        }
                    });

                } catch (Exception e) {}
            }
        }).start();
    }
}

final UIController controller = new UIController();
controller.renderHistoryList("");

searchHistoryField.addTextChangedListener(new android.text.TextWatcher() {
    @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
    @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
        controller.renderHistoryList(s.toString());
    }
    @Override public void afterTextChanged(android.text.Editable s) {}
});

inputField.addTextChangedListener(new android.text.TextWatcher() {
    @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
    @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
        controller.fetchSuggestions(s.toString());
    }
    @Override public void afterTextChanged(android.text.Editable s) {}
});

startNewBtn.setOnClickListener(new android.view.View.OnClickListener() {
    @Override
    public void onClick(android.view.View v) {
        controller.openChat(String.valueOf(System.currentTimeMillis()));
    }
});

backBtn.setOnClickListener(new android.view.View.OnClickListener() {
    @Override
    public void onClick(android.view.View v) {
        chatPage.setVisibility(android.view.View.GONE);
        listPage.setVisibility(android.view.View.VISIBLE);
        controller.renderHistoryList("");
    }
});

sendBtn.setOnClickListener(new android.view.View.OnClickListener() {
    @Override
    public void onClick(android.view.View v) {
        if (isAnimating[0]) {
            cancelRequested[0] = true;
            return;
        }

        suggestionsContainer.setVisibility(android.view.View.GONE);
        final String userText = inputField.getText().toString().trim();

        if (userText.isEmpty()) {
            android.widget.Toast.makeText(ChatbotActivity.this, "لطفاً متن یا موضوعی بنویسید", android.widget.Toast.LENGTH_SHORT).show();
            return;
        }

        final boolean isRTL = controller.isRTL(userText);
        controller.addBubble((isRTL ? "شما:\n" : "You:\n") + userText, null, null, true, true, true);
        inputField.setText("");

        final android.widget.TextView loadingTv = new android.widget.TextView(ChatbotActivity.this);
        loadingTv.setText(isRTL ? "Wikipedia Bot:\nدر حال جستجو..." : "Wikipedia Bot:\nSearching...");
        loadingTv.setTextSize(15);
        loadingTv.setTextColor(0xFFAAAAAA);
        loadingTv.setPadding(28, 20, 28, 20);

        android.graphics.drawable.GradientDrawable loadBg = new android.graphics.drawable.GradientDrawable();
        loadBg.setColor(0xFF262626);
        loadBg.setCornerRadius(24f);
        loadingTv.setBackground(loadBg);

        android.widget.LinearLayout.LayoutParams loadParams = new android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT);
        loadParams.setMargins(0, 10, 60, 10);
        loadingTv.setLayoutParams(loadParams);
        messagesBox.addView(loadingTv);

        chatScroll.post(new Runnable() {
            @Override
            public void run() {
                chatScroll.fullScroll(android.view.View.FOCUS_DOWN);
            }
        });

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    String domain = controller.getDomain(userText);
                    String encoded = java.net.URLEncoder.encode(userText, "UTF-8");

                    String urlString = "https://" + domain + "/w/api.php"
                        + "?action=query"
                        + "&prop=extracts|pageimages"
                        + "&pithumbsize=600"
                        + "&exintro=1"
                        + "&explaintext=1"
                        + "&format=json"
                        + "&redirects=1"
                        + "&titles=" + encoded;

                    java.net.URL url = new java.net.URL(urlString);
                    javax.net.ssl.HttpsURLConnection connection = (javax.net.ssl.HttpsURLConnection) url.openConnection();
                    connection.setRequestMethod("GET");
                    connection.setConnectTimeout(12000);
                    connection.setReadTimeout(12000);
                    connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36");

                    java.io.BufferedReader reader = new java.io.BufferedReader(
                        new java.io.InputStreamReader(connection.getInputStream(), "UTF-8"));
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) response.append(line);
                    reader.close();
                    connection.disconnect();

                    org.json.JSONObject json = new org.json.JSONObject(response.toString());
                    org.json.JSONObject pages = json.getJSONObject("query").getJSONObject("pages");
                    java.util.Iterator<String> keys = pages.keys();

                    final String pageId = keys.next();
                    org.json.JSONObject page = pages.getJSONObject(pageId);

                    final String titleText = page.optString("title", "");
                    final String extract = page.optString("extract", "");

                    String imageUrlTemp = null;
                    if (page.has("thumbnail")) {
                        imageUrlTemp = page.getJSONObject("thumbnail").optString("source", null);
                    }
                    final String imageUrl = imageUrlTemp;

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            messagesBox.removeView(loadingTv);

                            if (pageId.equals("-1") || extract.isEmpty()) {
                                String notFoundMsg = isRTL
                                    ? "Wikipedia Bot:\n\nمتأسفانه اطلاعاتی درباره این موضوع پیدا نشد."
                                    : "Wikipedia Bot:\n\nSorry, no information was found on this topic.";
                                controller.addBubble(notFoundMsg, null, null, false, true, true);
                            } else {
                                String botAnswer = "Wikipedia Bot:\n\n" + titleText + "\n\n" + extract;
                                controller.addBubble(botAnswer, imageUrl, titleText, false, true, true);
                            }
                        }
                    });

                } catch (Exception e) {
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            messagesBox.removeView(loadingTv);
                            String errorMsg = isRTL
                                ? "Wikipedia Bot:\n\nخطا در اتصال به اینترنت یا دریافت اطلاعات."
                                : "Wikipedia Bot:\n\nNetwork error or failed to retrieve data.";
                            controller.addBubble(errorMsg, null, null, false, true, true);
                        }
                    });
                }
            }
        }).start();
    }
});
