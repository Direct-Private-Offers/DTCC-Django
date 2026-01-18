from fastapi import HTTPException, status

def validate_settlement_authority(transaction_data):
    """
    Enforces SOP Section 5: Dual-Node Governance.
    Checks for TA Approval and Corporate Authorization.
    """
    ta_approved = transaction_data.get("ta_approval_node")
    corp_approved = transaction_data.get("corporate_approval_node")

    if not ta_approved or not corp_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Settlement blocked: Missing Dual-Node Authorization (TA or Corp)"
        )
    return True

def get_settled_nft(collection, target_token_id, auth_context):
    # 1. Verify authorities first
    validate_settlement_authority(auth_context)
    
    # 2. Filter for the specific tokenId (Your requirement: return only the match)
    nft = next((item for item in collection if item["tokenId"] == target_token_id), None)
    
    if not nft:
        raise HTTPException(status_code=404, detail="NFT TokenID not found")
        
    return nft
