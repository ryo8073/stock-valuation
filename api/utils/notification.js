// api/utils/notification.js

export async function notifyUpdate(updateInfo) {
  const notifications = [];
  
  try {
    // Slack通知
    if (process.env.SLACK_WEBHOOK_URL) {
      const slackResult = await sendSlackNotification(updateInfo);
      notifications.push({ type: 'slack', success: slackResult });
    }
    
    // メール通知
    if (process.env.EMAIL_SMTP_URL) {
      const emailResult = await sendEmailNotification(updateInfo);
      notifications.push({ type: 'email', success: emailResult });
    }
    
    // Webhook通知
    if (process.env.WEBHOOK_URL) {
      const webhookResult = await sendWebhookNotification(updateInfo);
      notifications.push({ type: 'webhook', success: webhookResult });
    }
    
    console.log('Update notifications sent:', notifications);
    return notifications;
    
  } catch (error) {
    console.error('Notification error:', error);
    throw error;
  }
}

export async function notifyError(errorInfo) {
  const notifications = [];
  
  try {
    // Slack通知
    if (process.env.SLACK_WEBHOOK_URL) {
      const slackResult = await sendSlackErrorNotification(errorInfo);
      notifications.push({ type: 'slack', success: slackResult });
    }
    
    // メール通知
    if (process.env.EMAIL_SMTP_URL) {
      const emailResult = await sendEmailErrorNotification(errorInfo);
      notifications.push({ type: 'email', success: emailResult });
    }
    
    console.log('Error notifications sent:', notifications);
    return notifications;
    
  } catch (error) {
    console.error('Error notification failed:', error);
    throw error;
  }
}

async function sendSlackNotification(updateInfo) {
  try {
    const message = {
      text: '🔄 国税庁データ更新完了',
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*国税庁データ更新が完了しました*`
          }
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*更新日時:*\n${new Date(updateInfo.timestamp).toLocaleString('ja-JP')}`
            },
            {
              type: 'mrkdwn',
              text: `*更新レコード数:*\n${updateInfo.recordCount}件`
            }
          ]
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*変更内容:*\n${updateInfo.changes.join(', ')}`
          }
        }
      ]
    };
    
    const response = await fetch(process.env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message)
    });
    
    return response.ok;
    
  } catch (error) {
    console.error('Slack notification error:', error);
    return false;
  }
}

async function sendSlackErrorNotification(errorInfo) {
  try {
    const message = {
      text: '❌ 国税庁データ更新エラー',
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*国税庁データ更新でエラーが発生しました*`
          }
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*エラー日時:*\n${new Date(errorInfo.timestamp).toLocaleString('ja-JP')}`
            },
            {
              type: 'mrkdwn',
              text: `*エラー内容:*\n${errorInfo.error}`
            }
          ]
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*スタックトレース:*\n\`\`\`${errorInfo.stack}\`\`\``
          }
        }
      ]
    };
    
    const response = await fetch(process.env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message)
    });
    
    return response.ok;
    
  } catch (error) {
    console.error('Slack error notification error:', error);
    return false;
  }
}

async function sendEmailNotification(updateInfo) {
  try {
    // メール送信ロジック（簡略化）
    // 実際の実装では、nodemailer などのライブラリを使用
    console.log('Email notification would be sent:', updateInfo);
    return true;
    
  } catch (error) {
    console.error('Email notification error:', error);
    return false;
  }
}

async function sendEmailErrorNotification(errorInfo) {
  try {
    // エラーメール送信ロジック（簡略化）
    console.log('Error email notification would be sent:', errorInfo);
    return true;
    
  } catch (error) {
    console.error('Error email notification error:', error);
    return false;
  }
}

async function sendWebhookNotification(updateInfo) {
  try {
    const response = await fetch(process.env.WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'StockValuatorPro/1.0'
      },
      body: JSON.stringify({
        event: 'tax_data_updated',
        timestamp: updateInfo.timestamp,
        changes: updateInfo.changes,
        record_count: updateInfo.recordCount
      })
    });
    
    return response.ok;
    
  } catch (error) {
    console.error('Webhook notification error:', error);
    return false;
  }
} 