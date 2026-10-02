import jenkins.model.Jenkins
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider

def j = Jenkins.get()
def realm = new HudsonPrivateSecurityRealm(false)
realm.createAccount('student', System.getenv('JENKINS_ADMIN_PASSWORD'))
j.setSecurityRealm(realm)
def auth = new FullControlOnceLoggedInAuthorizationStrategy()
auth.setAllowAnonymousRead(false)
j.setAuthorizationStrategy(auth)
j.setNumExecutors(1)
def credentials = SystemCredentialsProvider.getInstance().getCredentials()
credentials.removeAll { it.id == 'sonar-login' }
credentials.add(new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,
    'sonar-login', 'Local SonarQube account', 'admin', System.getenv('SONAR_ADMIN_PASSWORD')))
SystemCredentialsProvider.getInstance().save()
def job = j.getItem('sit753-decents') ?: j.createProject(WorkflowJob, 'sit753-decents')
job.setDefinition(new CpsFlowDefinition(new File(System.getenv('PROJECT_DIR'), 'Jenkinsfile').text, true))
job.save()
j.save()
