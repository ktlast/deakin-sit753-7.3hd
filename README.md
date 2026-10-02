# Decents 分帳計算 API

使用 FastAPI 驗證共同支出資料，並計算每位成員的分帳金額。
程式使用 Decents 的部分支出驗證與計算邏輯。每次請求提供完整的品項
和成員資料，服務不儲存資料。

## 啟動

需要 Docker（含 Compose）、Python 3 和 Git。下載映像與套件時需要網路。
Apple Silicon 上的 SonarScanner 使用 amd64 模擬執行。

以下指令用於第一次啟動新環境，請在 repo 根目錄執行：

```sh
python3 scripts/init-local.py
docker compose up -d --build
python3 scripts/manage.py setup-sonar
python3 scripts/manage.py update
python3 scripts/manage.py run
```

第一次啟動可能需要幾分鐘。等 Jenkins 登入頁出現後，再執行
`manage.py update`。後續可以在 Jenkins 按 **Build Now** 執行 pipeline。

登入資料保存在未追蹤的 `.env`：

| 服務 | 帳號 | 密碼欄位 |
|---|---|---|
| Jenkins | `student` | `JENKINS_ADMIN_PASSWORD` |
| SonarQube | `admin` | `SONAR_ADMIN_PASSWORD` |

若既有環境使用其他 runtime 目錄，請使用該目錄的 `.env`，不要重新產生
另一份設定。Compose 和 `manage.py` 都接受 `--env-file`。
例如 `docker compose --env-file /path/to/runtime/.env up -d` 與
`python3 scripts/manage.py status --env-file /path/to/runtime/.env`。
建立新 runtime 目錄則使用 `init-local.py --runtime-dir /path/to/runtime`。

| 服務 | 網址 |
|---|---|
| Jenkins | http://localhost:18080/job/sit753-decents/ |
| SonarQube | http://localhost:19000/dashboard?id=sit753-decents |
| Test API | http://localhost:18081/docs |
| Production API | http://localhost:18082/docs |

容器使用固定的本機名稱與連接埠，同時間只啟動一份環境。

## API

| Endpoint | 用途 |
|---|---|
| `GET /health` | 查看服務狀態與環境名稱 |
| `POST /items/validate` | 驗證支出或轉帳資料 |
| `POST /balances/calculate` | 計算各成員已付、應付與淨額 |

支援權重分攤、指定匯率換算與小數精度處理。匯率由呼叫端提供，不會
查詢即時匯率。不符合格式或規則的請求回傳 HTTP 422。

範例位於 `app/examples`。可以貼到 Swagger 的 **Try it out**，或執行：

```sh
curl http://localhost:18081/health
curl -H 'Content-Type: application/json' --data-binary @app/examples/item.json http://localhost:18081/items/validate
curl -H 'Content-Type: application/json' --data-binary @app/examples/balances.json http://localhost:18082/balances/calculate
```

範例中 Alice 支付 AUD 120，與 Bob 平分。Alice 的淨額為 -60（應收），
Bob 的淨額為 60（應付）。

## Jenkins pipeline

| 階段 | 執行內容 |
|---|---|
| Build | 建立並標記 Docker image，保存建置產物 |
| Test | 對建好的 API 執行元件與 HTTP 測試 |
| Code Quality | 用 SonarQube 分析程式與 coverage，等待 Quality Gate 結果 |
| Security | 用 Trivy 掃描映像及已安裝依賴 |
| Deploy | 部署到 test，檢查 health 和實際分帳計算 |
| Release | 將同一映像部署到本機 production 並驗證 |

測試、Quality Gate 或安全檢查失敗時，pipeline 會停止。Test 和 production
使用不同容器、環境名稱及連接埠，從測試到 release 不會重新建置映像。
Jenkins 保存測試結果、coverage、掃描報告、部署檢查與映像。

Quality Gate 要求 maintainability 至少 B、reliability 至少 C、重複程式碼
不超過 10%。新程式碼也檢查 issues、coverage 和 duplication。指標與結果
可在 SonarQube 和建置產物查看。目前手動啟動，沒有設定 Git push trigger。

若新 production 容器未通過啟動檢查，Release 可以恢復上一個映像。
這個 fallback 尚未透過故障模擬驗證。

## 測試範圍

測試包含支出與轉帳驗證、權重分攤、匯率換算、小數精度和 HTTP 回應。
HTTP 案例分別在程式內及執行中的容器測試，結果只代表這個 API 的範圍。

## 安全檢查

Trivy 報告列出漏洞 ID、嚴重程度、安裝版本及修正版本。
未接受的 HIGH 和 CRITICAL 漏洞會阻擋 pipeline。

`security-exceptions.json` 記錄掃描當時沒有修正版本的特定 OS 套件、
接受理由、參考資料與到期日。只有符合紀錄的 OS HIGH 漏洞可接受；
已提供修正、例外到期及 CRITICAL 漏洞仍會阻擋。例外限於本機容器。

API 使用非 root 帳號，移除 capabilities 並啟用 no-new-privileges，沒有
掛載主機檔案或 Docker socket，連接埠只開放 localhost。這些措施降低
風險，但不代表漏洞套件已修復。

## 查看結果與停止服務

使用預設 runtime 時：

```sh
python3 scripts/manage.py status
python3 scripts/manage.py log
docker compose stop
docker stop sit753-decents-test sit753-decents-prod
```

若使用其他 runtime，前面三個指令需要加上對應的 `--env-file`。
報告位於 runtime 的 `workspace/results` 和 Jenkins artifacts。
API 容器由 pipeline 另外建立，因此使用最後一個指令停止。
