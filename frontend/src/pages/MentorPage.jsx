/**
 * SkillTree AI - Mentor Page
 * Find mentors and manage mentorship relationships
 * @module pages/MentorPage
 */

import { useEffect, useState } from 'react';
import * as mentorApi from '../api/mentorApi';
import { formatXP } from '../utils/constants';

/**
 * Mentor page component
 * @returns {JSX.Element} Mentor page
 */
function MentorPage() {
  const [mentors, setMentors] = useState([]);
  const [myMentors, setMyMentors] = useState([]);
  const [myMentees, setMyMentees] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('find');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  /**
   * Fetch all mentor data
   */
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [mentorsData, myMentorsData, myMenteesData, specialtiesData] = await Promise.all([
        mentorApi.getMentors(),
        mentorApi.getMyMentors().catch(() => []),
        mentorApi.getMyMentees().catch(() => []),
        mentorApi.getMentorSpecialties().catch(() => []),
      ]);
      
      setMentors(mentorsData.results || mentorsData);
      setMyMentors(myMentorsData);
      setMyMentees(myMenteesData);
      setSpecialties(specialtiesData);
    } catch (e) {
      setError('Failed to load mentor data');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle mentorship request
   * @param {number|string} mentorId - Mentor ID
   */
  const handleRequestMentorship = async (mentorId) => {
    try {
      await mentorApi.requestMentorship(mentorId, 'I would like to learn from you!');
      alert('Mentorship request sent!');
      fetchData();
    } catch (e) {
      alert('Failed to send request');
    }
  };

  /**
   * Handle end mentorship
   * @param {number|string} mentorshipId - Mentorship ID
   */
  const handleEndMentorship = async (mentorshipId) => {
    if (!confirm('Are you sure you want to end this mentorship?')) return;
    
    try {
      await mentorApi.endMentorship(mentorshipId);
      fetchData();
    } catch (e) {
      alert('Failed to end mentorship');
    }
  };

  /**
   * Filter mentors by search and specialty
   * @returns {Array} Filtered mentors
   */
  const filteredMentors = mentors.filter((mentor) => {
    const matchesSearch = !searchQuery || 
      mentor.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mentor.specialty?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesSpecialty = !selectedSpecialty || mentor.specialty === selectedSpecialty;
    
    return matchesSearch && matchesSpecialty;
  });

  return (
    <div className="mentor-page">
      <div className="mentor-header">
        <h1>Mentorship</h1>
        <p className="header-subtitle">Learn from experienced developers or become a mentor</p>
      </div>

      {/* Tabs */}
      <div className="mentor-tabs">
        <button
          className={`tab ${activeTab === 'find' ? 'active' : ''}`}
          onClick={() => setActiveTab('find')}
        >
          Find Mentors
        </button>
        <button
          className={`tab ${activeTab === 'my-mentors' ? 'active' : ''}`}
          onClick={() => setActiveTab('my-mentors')}
        >
          My Mentors ({myMentors.length})
        </button>
        <button
          className={`tab ${activeTab === 'my-mentees' ? 'active' : ''}`}
          onClick={() => setActiveTab('my-mentees')}
        >
          My Mentees ({myMentees.length})
        </button>
      </div>

      {/* Find Mentors Tab */}
      {activeTab === 'find' && (
        <div className="find-mentors-tab">
          {/* Search and Filters */}
          <div className="search-filters">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search mentors..."
              className="search-input"
            />
            <select
              value={selectedSpecialty}
              onChange={(e) => setSelectedSpecialty(e.target.value)}
              className="filter-select"
            >
              <option value="">All Specialties</option>
              {specialties.map((specialty) => (
                <option key={specialty} value={specialty}>{specialty}</option>
              ))}
            </select>
          </div>

          {/* Mentors Grid */}
          {isLoading ? (
            <div className="loading-message">Loading mentors...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : filteredMentors.length === 0 ? (
            <div className="empty-message">No mentors found</div>
          ) : (
            <div className="mentors-grid">
              {filteredMentors.map((mentor) => (
                <div key={mentor.id} className="glass-panel mentor-card">
                  <div className="mentor-avatar">
                    {mentor.avatar ? (
                      <img src={mentor.avatar} alt={mentor.username} />
                    ) : (
                      <span>👨‍🏫</span>
                    )}
                  </div>
                  <h3>{mentor.username}</h3>
                  <p className="mentor-specialty">{mentor.specialty || 'General'}</p>
                  
                  <div className="mentor-stats">
                    <div className="stat">
                      <span className="stat-value">Level {mentor.level}</span>
                      <span className="stat-label">Level</span>
                    </div>
                    <div className="stat">
                      <span className="stat-value">{formatXP(mentor.xp)}</span>
                      <span className="stat-label">XP</span>
                    </div>
                    <div className="stat">
                      <span className="stat-value">{mentor.menteesCount || 0}</span>
                      <span className="stat-label">Mentees</span>
                    </div>
                  </div>
                  
                  <p className="mentor-bio">{mentor.bio || 'No bio available'}</p>
                  
                  <button
                    onClick={() => handleRequestMentorship(mentor.id)}
                    className="request-button primary-cta"
                  >
                    Request Mentorship
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* My Mentors Tab */}
      {activeTab === 'my-mentors' && (
        <div className="my-mentors-tab">
          {myMentors.length === 0 ? (
            <div className="empty-message glass-panel">
              <p>You don't have any mentors yet.</p>
              <button onClick={() => setActiveTab('find')} className="primary-cta">
                Find a Mentor
              </button>
            </div>
          ) : (
            <div className="mentorship-list">
              {myMentors.map((mentorship) => (
                <div key={mentorship.id} className="glass-panel mentorship-card">
                  <div className="mentor-info">
                    <div className="mentor-avatar">
                      {mentorship.mentor?.avatar ? (
                        <img src={mentorship.mentor.avatar} alt={mentorship.mentor.username} />
                      ) : (
                        <span>👨‍🏫</span>
                      )}
                    </div>
                    <div className="mentor-details">
                      <h3>{mentorship.mentor?.username}</h3>
                      <p>Since {new Date(mentorship.startedAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="mentorship-actions">
                    <button className="secondary-cta">Message</button>
                    <button 
                      onClick={() => handleEndMentorship(mentorship.id)}
                      className="secondary-cta danger"
                    >
                      End
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* My Mentees Tab */}
      {activeTab === 'my-mentees' && (
        <div className="my-mentees-tab">
          {myMentees.length === 0 ? (
            <div className="empty-message glass-panel">
              <p>You don't have any mentees yet.</p>
              <p>Complete more quests and level up to become a mentor!</p>
            </div>
          ) : (
            <div className="mentorship-list">
              {myMentees.map((mentorship) => (
                <div key={mentorship.id} className="glass-panel mentorship-card">
                  <div className="mentee-info">
                    <div className="mentor-avatar">
                      {mentorship.mentee?.avatar ? (
                        <img src={mentorship.mentee.avatar} alt={mentorship.mentee.username} />
                      ) : (
                        <span>👨‍🎓</span>
                      )}
                    </div>
                    <div className="mentor-details">
                      <h3>{mentorship.mentee?.username}</h3>
                      <p>Since {new Date(mentorship.startedAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="mentorship-actions">
                    <button className="secondary-cta">Message</button>
                    <button 
                      onClick={() => handleEndMentorship(mentorship.id)}
                      className="secondary-cta danger"
                    >
                      End
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MentorPage;