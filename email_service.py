"""
Service d'envoi d'emails avec SendGrid
"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY non configurée. Les emails ne pourront pas être envoyés.")
        
        self.from_email = os.environ.get('FROM_EMAIL', 'no-reply@camerasystem.local')
        self.sg = SendGridAPIClient(self.api_key) if self.api_key else None
    
    def send_email(self, to_email, subject, text_content=None, html_content=None):
        """Envoie un email"""
        if not self.sg:
            logger.error("Service email non configuré. Impossible d'envoyer l'email.")
            return False
        
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject
            )
            
            if html_content:
                message.content = Content("text/html", html_content)
            elif text_content:
                message.content = Content("text/plain", text_content)
            else:
                logger.error("Aucun contenu fourni pour l'email")
                return False
            
            response = self.sg.send(message)
            logger.info(f"Email envoyé avec succès à {to_email}. Status: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {e}")
            return False
    
    def send_equipment_offline_alert(self, client_email, client_name, equipment_name, equipment_type, equipment_ip):
        """Envoie une alerte d'équipement hors ligne"""
        subject = f"🚨 Alerte Équipement Hors Ligne - {equipment_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545, #c82333); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">⚠️ Alerte Équipement</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Système de Surveillance Caméras</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                    <h2 style="color: #dc3545; margin-top: 0;">Équipement Déconnecté</h2>
                    
                    <p>Bonjour <strong>{client_name}</strong>,</p>
                    
                    <p>Nous vous informons qu'un de vos équipements de surveillance s'est déconnecté :</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 6px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; width: 120px;">Nom :</td>
                                <td style="padding: 8px 0;">{equipment_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Type :</td>
                                <td style="padding: 8px 0;">{equipment_type}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Adresse IP :</td>
                                <td style="padding: 8px 0;">{equipment_ip}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Statut :</td>
                                <td style="padding: 8px 0; color: #dc3545; font-weight: bold;">🔴 Hors Ligne</td>
                            </tr>
                        </table>
                    </div>
                    
                    <h3>Actions Recommandées :</h3>
                    <ul style="color: #495057;">
                        <li>Vérifiez la connexion réseau de l'équipement</li>
                        <li>Contrôlez l'alimentation électrique</li>
                        <li>Redémarrez l'équipement si nécessaire</li>
                        <li>Contactez le support technique si le problème persiste</li>
                    </ul>
                    
                    <div style="margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 6px; text-align: center;">
                        <p style="margin: 0; color: #6c757d; font-size: 14px;">
                            Cet email a été envoyé automatiquement par le système de surveillance.<br>
                            Pour plus d'informations, connectez-vous à votre interface de monitoring.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(client_email, subject, html_content=html_content)
    
    def send_account_approval_notification(self, user_email, user_name, approved=True):
        """Envoie une notification d'approbation/refus de compte"""
        if approved:
            subject = "✅ Votre compte a été approuvé - Camera Monitor"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                        <h1 style="margin: 0; font-size: 24px;">✅ Compte Approuvé</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Camera Monitor System</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                        <h2 style="color: #28a745; margin-top: 0;">Bienvenue !</h2>
                        
                        <p>Bonjour <strong>{user_name}</strong>,</p>
                        
                        <p>Nous sommes heureux de vous informer que votre demande de compte a été <strong>approuvée</strong> par notre équipe administrative.</p>
                        
                        <p>Vous pouvez maintenant vous connecter à votre interface de monitoring et commencer à gérer vos équipements de surveillance.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">
                                Se Connecter
                            </a>
                        </div>
                        
                        <p>Si vous avez des questions, n'hésitez pas à contacter notre support technique.</p>
                        
                        <p>Cordialement,<br>L'équipe Camera Monitor</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = "❌ Votre demande de compte a été refusée - Camera Monitor"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #dc3545, #c82333); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                        <h1 style="margin: 0; font-size: 24px;">❌ Demande Refusée</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Camera Monitor System</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                        <h2 style="color: #dc3545; margin-top: 0;">Demande Non Approuvée</h2>
                        
                        <p>Bonjour <strong>{user_name}</strong>,</p>
                        
                        <p>Nous vous informons que votre demande de compte n'a pas pu être approuvée à ce moment.</p>
                        
                        <p>Pour plus d'informations concernant cette décision ou pour soumettre une nouvelle demande, nous vous invitons à contacter directement notre équipe administrative.</p>
                        
                        <p>Cordialement,<br>L'équipe Camera Monitor</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return self.send_email(user_email, subject, html_content=html_content)

# Instance globale du service email
email_service = EmailService()