document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const repoUrl = document.getElementById('repo-url').value;
        
        if (!repoUrl) {
            alert('Please enter a repository URL');
            return;
        }
        
        const analyzeBtn = document.getElementById('analyze-btn');
        analyzeBtn.textContent = 'Analyzing...';
        analyzeBtn.disabled = true;
        
        try {
            // This will be implemented later
            alert('Repository analysis will be implemented in the next phase');
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during analysis');
        } finally {
            analyzeBtn.textContent = 'Analyze Codebase';
            analyzeBtn.disabled = false;
        }
    });
});
